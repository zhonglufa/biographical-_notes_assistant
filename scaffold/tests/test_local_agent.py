"""test_local_agent.py — 本机 Agent 投递编排核心测试（B1）

验证：规划过滤（排除 low）/ 半自动确认闸门 / 限额 / 幂等 / 验证码暂停 /
      事件发布对齐 domain-events 契约（apply.status.changed）。
零外部依赖，直接 `python scaffold/tests/test_local_agent.py` 运行。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from base import check
from local_agent import (
    DeliveryOrchestrator, DeliveryStrategy, JobCandidate, MatchBand, MockAdapter,
)
from event_bus import EventBus  # 真实事件总线，验证契约对齐


def _jobs():
    return [
        JobCandidate("J1", "Java后端", "A厂", MatchBand.HIGH, 0.92, "BOSS"),
        JobCandidate("J2", "Java开发", "B厂", MatchBand.MEDIUM, 0.71, "猎聘"),
        JobCandidate("J3", "前端", "C厂", MatchBand.LOW, 0.30, "智联"),
    ]


def test_plan_filters_low():
    print("· 规划过滤排除 low 匹配")
    orch = DeliveryOrchestrator(MockAdapter())
    cands = orch.plan(_jobs(), DeliveryStrategy(min_band=MatchBand.MEDIUM))
    ids = {c.job_id for c in cands}
    check("low 匹配 J3 被排除", "J3" not in ids)
    check("high/medium J1/J2 保留", {"J1", "J2"} <= ids)
    check("按匹配度降序（J1 在前）", cands[0].job_id == "J1")


def test_confirmation_gate():
    print("· 半自动确认闸门：未确认绝不执行")
    orch = DeliveryOrchestrator(MockAdapter())
    strat = DeliveryStrategy(require_confirmation=True)
    cands = orch.plan(_jobs(), strat)
    # 只确认 J1，不确认 J2
    outs = orch.execute(cands, confirmed_ids={"J1"}, strategy=strat)
    by = {o.job_id: o for o in outs}
    check("J1 已投递", by["J1"].status == "applied")
    check("J2 未确认 -> skipped_unconfirmed", by["J2"].status == "skipped_unconfirmed")


def test_quota_and_idempotency():
    print("· 当日限额 + 幂等去重")
    adapter = MockAdapter()
    orch = DeliveryOrchestrator(adapter)
    strat = DeliveryStrategy(daily_quota=1, require_confirmation=False)
    cands = orch.plan(_jobs(), strat)
    outs1 = orch.execute(cands, confirmed_ids={"J1", "J2"}, strategy=strat)
    by1 = {o.job_id: o for o in outs1}
    check("限额内 J1 投递", by1["J1"].status == "applied")
    check("达限额 J2 -> skipped_quota", by1["J2"].status == "skipped_quota")
    # 二次执行：J1 已投过 -> 幂等去重
    outs2 = orch.execute(cands, confirmed_ids={"J1"}, strategy=strat)
    by2 = {o.job_id: o for o in outs2}
    check("J1 二次 -> skipped_duplicate（幂等）", by2["J1"].status == "skipped_duplicate")


def test_captcha_pause():
    print("· 验证码暂停（不失败、不卡死）")
    orch = DeliveryOrchestrator(MockAdapter(captcha_jobs={"J2"}))
    strat = DeliveryStrategy(require_confirmation=False)
    cands = orch.plan(_jobs(), strat)
    outs = orch.execute(cands, confirmed_ids={"J1", "J2"}, strategy=strat)
    by = {o.job_id: o for o in outs}
    check("J2 验证码 -> pending_captcha", by["J2"].status == "pending_captcha")
    check("J1 正常投递", by["J1"].status == "applied")


def test_event_contract_alignment():
    print("· 事件发布对齐 domain-events 契约")
    bus = EventBus()
    published = []
    bus.subscribe("apply.status.changed", lambda p: published.append(p))
    orch = DeliveryOrchestrator(MockAdapter(), bus=bus, user_id="U-test")
    # 半自动闸门：仅确认 J1 -> 仅 J1 投递并发布事件（J2 未确认不执行、不发布）
    strat = DeliveryStrategy(require_confirmation=True)
    cands = orch.plan(_jobs(), strat)
    orch.execute(cands, confirmed_ids={"J1"}, strategy=strat)
    check("仅确认项发布事件（1 条）", len(published) == 1)
    check("事件过 domain-events 契约（bus 接受）", bus.log_size() == 1)
    p = published[0]
    check("platformId 映射为枚举 boss", p["platformId"] == "boss")
    check("toState=submitted", p["toState"] == "submitted")
    check("userId 透传", p["userId"] == "U-test")


def main():
    print("=== test_local_agent ===")
    test_plan_filters_low()
    test_confirmation_gate()
    test_quota_and_idempotency()
    test_captcha_pause()
    test_event_contract_alignment()
    print("本机 Agent 投递核心测试通过 ✅")


if __name__ == "__main__":
    main()
