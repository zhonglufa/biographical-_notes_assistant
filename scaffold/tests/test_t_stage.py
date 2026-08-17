"""
test_t_stage.py — T 阶段真实测试闭环（QA 主导 · 补强 B 新增）

本文件是 T 阶段「真实测试闭环」的**权威收敛文件**，区别于早期 B 阶段的
「冒烟 + 设计一致性」测试：这里跑的是**功能 / 集成 / 契约回归**三件套，
直接对应 PROJECT_BRAIN §1 V/T/O 七阶段中 T 阶段（T1/T2/T3）。

  T1 功能测试：本机 Agent 投递编排核心安全属性（幂等 / 限额 / 半自动确认闸门 /
      验证码暂停）+ 服务端状态机（submitted/closed）+ 事件总线 fail-closed +
      护栏 2（LLM 成本硬上限 + 熔断）+ 护栏 3（封号率监控阈值告警）。
  T2 集成测试：本机 Agent + 服务端 API + 前端三联调一致性——
      ① 后端注册表 A 编号集合 == 前端 api.js ENDPOINTS A 编号集合（25 对 25）；
      ② 前端组件实际读取的字段，后端 example 响应必须提供（契约对齐，非仅类型）。
  T3 契约回归：25 端点 example_request 全过 response_schema（契约优先、fail-closed
      500 暴露「实现偏离契约」）；并验证响应侧 fail-closed 机制本身可用。

零外部依赖（仅标准库），直接 `python scaffold/tests/test_t_stage.py` 运行。
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from base import check

# —— 被测模块 ——
from contract_runtime import ContractRuntime
from stubs import API_STUB
from stubs.core import Endpoint
from local_agent import DeliveryOrchestrator, DeliveryStrategy, JobCandidate, MatchBand, MockAdapter
from event_bus import EventBus
from server_app import ServerApp
from delivery_state_machine import DeliveryStateMachine
from metrics import InMemoryMetrics
from cost_policy import BudgetPolicy
from monitor import LightweightMonitor, MonitorThresholds, BanTracker, ApplyLedger


# ---------------------------------------------------------------------------
# T1 · 功能测试
# ---------------------------------------------------------------------------
def _jobs():
    return [
        JobCandidate("J1", "Java后端", "A厂", MatchBand.HIGH, 0.92, "BOSS"),
        JobCandidate("J2", "Java开发", "B厂", MatchBand.MEDIUM, 0.71, "猎聘"),
        JobCandidate("J3", "前端", "C厂", MatchBand.LOW, 0.30, "智联"),
    ]


def test_t1_delivery_core_safety():
    print("· T1 本机 Agent 投递核心安全属性")
    # 半自动确认闸门：未确认绝不执行
    orch = DeliveryOrchestrator(MockAdapter())
    strat = DeliveryStrategy(require_confirmation=True)
    cands = orch.plan(_jobs(), strat)
    outs = orch.execute(cands, confirmed_ids={"J1"}, strategy=strat)
    by = {o.job_id: o for o in outs}
    check("确认项 J1 -> applied", by["J1"].status == "applied")
    check("未确认 J2 -> skipped_unconfirmed（绝不静默执行）", by["J2"].status == "skipped_unconfirmed")

    # 当日限额 + 幂等去重
    orch2 = DeliveryOrchestrator(MockAdapter())
    strat2 = DeliveryStrategy(daily_quota=1, require_confirmation=False)
    c2 = orch2.plan(_jobs(), strat2)
    o1 = orch2.execute(c2, confirmed_ids={"J1", "J2"}, strategy=strat2)
    b1 = {o.job_id: o for o in o1}
    check("限额内 J1 -> applied", b1["J1"].status == "applied")
    check("达日限额 J2 -> skipped_quota", b1["J2"].status == "skipped_quota")
    o2 = orch2.execute(c2, confirmed_ids={"J1"}, strategy=strat2)
    b2 = {o.job_id: o for o in o2}
    check("同岗二次 -> skipped_duplicate（幂等，不重复投递）", b2["J1"].status == "skipped_duplicate")

    # 验证码暂停：不失败、不卡死、不越权执行
    orch3 = DeliveryOrchestrator(MockAdapter(captcha_jobs={"J2"}))
    strat3 = DeliveryStrategy(require_confirmation=False)
    c3 = orch3.plan(_jobs(), strat3)
    o3 = orch3.execute(c3, confirmed_ids={"J1", "J2"}, strategy=strat3)
    b3 = {o.job_id: o for o in o3}
    check("J2 触发验证码 -> pending_captcha（需人工处理）", b3["J2"].status == "pending_captcha")
    check("J1 同时正常 -> applied", b3["J1"].status == "applied")

    # low 匹配被规划过滤排除（不浪费配额/不触平台）
    plan = orch.plan(_jobs(), DeliveryStrategy(min_band=MatchBand.MEDIUM))
    ids = {c.job_id for c in plan}
    check("low 匹配 J3 被排除", "J3" not in ids)
    check("high/medium 保留且按匹配度降序", plan[0].job_id == "J1")


def test_t1_server_state_machine():
    print("· T1 服务端投递状态机")
    bus = EventBus()
    sm = DeliveryStateMachine()
    app = ServerApp(bus=bus, metrics=InMemoryMetrics(), state_machine=sm)
    tid = app.create_application("u1", "j1", "boss")
    check("create -> autofilling", sm.state(tid) == "autofilling")
    app.record_submission(tid)
    check("record_submission -> submitted", sm.state(tid) == "submitted")
    tid2 = app.create_application("u1", "j2", "boss")
    app.record_failure(tid2)
    check("record_failure -> closed", sm.state(tid2) == "closed")
    # 已 submitted 的 tid 再提交应被状态机拒绝（自环不允许），且不重复发布事件
    captured = []
    bus.subscribe("apply.status.changed", lambda p: captured.append(p))
    raised = False
    try:
        app.record_submission(tid)  # tid 已是 submitted
    except Exception:
        raised = True
    check("已 submitted 重复跃迁被状态机拒绝（自环不允许，防误触发）", raised is True)
    check("拒绝后未产生重复事件（事件与合法跃迁一一对应）", len(captured) == 0)


def test_t1_event_bus_fail_closed():
    print("· T1 事件总线 fail-closed")
    bus = EventBus()
    got = []
    bus.subscribe("payment.status.changed", lambda p: got.append(p))
    ok, _ = bus.publish(__import__("event_bus").build_payment_status_event("O1", "U1", "paid", 29900))
    check("合法支付事件发布成功", ok is True and len(got) == 1)
    ok2, _ = bus.publish(__import__("event_bus").build_payment_status_event("O2", "U1", "paid", -1))
    check("非法金额事件被拒(fail-closed, 不入审计)", ok2 is False and len(got) == 1)


def test_t1_guardrail2_cost_circuit():
    print("· T1 护栏 2：LLM 成本硬上限 + 熔断")
    pol = BudgetPolicy(now=lambda: 1000)
    check("默认日硬上限 ¥500(50000分) 装配到位", pol.daily_cap_cents == 50_000)
    check("熔断器初始闭合(is_open=False)", pol.is_open() is False)
    # 模拟累计成本逼近/超过上限
    for _ in range(6000):  # 6000 * 10分 = 60000分 > 50000 上限
        pol.guard().charge(10)
    check("超日硬上限后熔断器打开（熔断生效）", pol.is_open() is True)
    check("剩余额度不为正（已达/超上限）", pol.remaining_cents() <= 0)


def test_t1_guardrail3_ban_monitor():
    print("· T1 护栏 3：封号率监控阈值告警")
    mon = LightweightMonitor(thresholds=MonitorThresholds(ban_rate_max=0.02))
    mon.bans.set_active_accounts(100)
    mon.record_ban(1)  # 1/100 = 1% < 2% 阈值
    check("封号率 1% 不告警", "ban_rate_high" not in mon.snapshot()["alerts"])
    mon.record_ban(2)  # 3/100 = 3% > 2% 阈值
    check("封号率 3% 触发 ban_rate_high 告警", "ban_rate_high" in mon.snapshot()["alerts"])
    # 投递成功率低于 80% 告警
    led = ApplyLedger()
    for _ in range(2):
        led.record(True)
    led.record(False)  # 2/3 ≈ 66.7% < 80%
    mon.applies = led
    check("投递成功率 < 80% 触发 apply_success_low 告警", "apply_success_low" in mon.snapshot()["alerts"])


# ---------------------------------------------------------------------------
# T2 · 集成测试（本机 Agent + 服务端 + 前端三联调一致性）
# ---------------------------------------------------------------------------
def _frontend_endpoint_acodes():
    """从前端 api.js 解析出 ENDPOINTS 里声明的 A 编号集合（静态解析，零依赖）。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                        "frontend", "src", "lib", "api.js")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return set(re.findall(r"A\d{2}\b", text))


def test_t2_backend_frontend_endpoint_parity():
    print("· T2 后端注册表 A 编号 == 前端 api.js ENDPOINTS A 编号")
    backend = {name.split()[0] for name in API_STUB.endpoint_ids()}  # "A01 auth-login" -> "A01"
    frontend = _frontend_endpoint_acodes()
    check("后端 25 端点 A 编号齐全", len(backend) == 25)
    check("前端 api.js 声明 25 端点 A 编号齐全", len(frontend) == 25)
    check("前后端 A 编号集合完全一致（25 对 25，无缺漏/无多余）", backend == frontend)


def test_t2_consumed_fields_present():
    print("· T2 前端已消费字段 == 后端 example 响应字段（契约对齐）")
    rt = ContractRuntime()

    # A22 通知列表：Notifications.jsx 读取 items[].{id,level,title,body,read,createdAt,channel} + unread
    r22 = rt.call("A22 notifications-list", {})
    check("A22 响应 200 + 契约未破坏", r22.status == 200 and r22.contract_breach is False)
    items = r22.body.get("items", [])
    check("A22 items 为非空数组", isinstance(items, list) and len(items) > 0)
    it = items[0]
    for fld in ("id", "level", "title", "body", "read", "createdAt", "channel"):
        check(f"A22 item 含前端读取字段 '{fld}'", fld in it)
    check("A22 含 unread 计数", "unread" in r22.body and isinstance(r22.body["unread"], int))

    # A24 每日日报：U9 组件读取 stats.{appliedTotal,success,failed,byPlatform,hrViews,interviewInvites,newQuestions,trend7d}
    r24 = rt.call("A24 daily-report-today", {})
    check("A24 响应 200 + 契约未破坏", r24.status == 200 and r24.contract_breach is False)
    stats = r24.body.get("stats", {})
    for fld in ("appliedTotal", "success", "failed", "byPlatform", "hrViews",
                "interviewInvites", "newQuestions", "trend7d"):
        check(f"A24 stats 含前端读取字段 '{fld}'", fld in stats)
    check("A24 byPlatform 为数组且元素含 platformId/count",
          isinstance(stats.get("byPlatform"), list) and "platformId" in stats["byPlatform"][0])

    # A01/A03 登录/权益：Auth/Account 组件读取 accessToken / plan / quotaUsed / quotaLimit
    r01 = rt.call("A01 auth-login", {"channel": "email", "deviceId": "dev-x",
                                     "email": "user@x.com", "password": "secret123"})
    check("A01 响应 200 + 含 accessToken(userId/plan)", r01.status == 200 and "accessToken" in r01.body)
    r03 = rt.call("A03 users-me", {})
    check("A03 响应 200", r03.status == 200)
    for fld in ("userId", "plan", "quotaUsed", "quotaLimit"):
        check(f"A03 含前端读取字段 '{fld}'", fld in r03.body)


# ---------------------------------------------------------------------------
# T3 · 契约回归
# ---------------------------------------------------------------------------
def test_t3_all_endpoints_response_schema():
    print("· T3 25 端点 example_request 全过 response_schema")
    rt = ContractRuntime()
    results = rt.validate_all_examples()
    check("覆盖全部 25 端点", len(results) == 25)
    bad = [name for name, r in results.items()
           if r.status != 200 or r.contract_breach is True]
    check("所有端点 example 响应 200 且未破坏响应契约", len(bad) == 0)
    if bad:
        print("    偏离契约端点:", bad)


def test_t3_response_fail_closed_mechanism():
    print("· T3 响应侧 fail-closed 机制可用（实现偏离契约 -> 500 暴露）")
    # 构造一个响应契约违规的探针端点，验证 Endpoint.dispatch 会 500 而非吞掉
    probe = Endpoint("T3-probe", None, "auth-login.response.schema.json",
                     lambda r: {"THIS_FIELD_IS_NOT_IN_SCHEMA": 1})
    code, body = probe.dispatch({})
    check("响应契约违规 -> 500 + response_schema_violation",
          code == 500 and body.get("error") == "response_schema_violation")


# ---------------------------------------------------------------------------
# 运行入口
# ---------------------------------------------------------------------------
def main():
    print("=== T 阶段真实测试闭环（test_t_stage）===")
    # T1
    test_t1_delivery_core_safety()
    test_t1_server_state_machine()
    test_t1_event_bus_fail_closed()
    test_t1_guardrail2_cost_circuit()
    test_t1_guardrail3_ban_monitor()
    # T2
    test_t2_backend_frontend_endpoint_parity()
    test_t2_consumed_fields_present()
    # T3
    test_t3_all_endpoints_response_schema()
    test_t3_response_fail_closed_mechanism()
    print(f"\nT 阶段测试全部通过 ✅ （T1 功能 / T2 集成 / T3 契约回归）")


if __name__ == "__main__":
    main()
