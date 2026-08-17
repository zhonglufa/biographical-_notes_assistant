"""
test_smoke.py — 冒烟测试（零外部依赖，仅标准库）

验证三件事：
  1) 契约加载/校验可用（contract_runtime）
  2) 事件发布前的契约校验 fail-closed（event_bus）
  3) 接口分发的契约校验 fail-closed（stubs 注册表）

关键改动（解耦后）：测试**完全基于注册表**遍历所有端点，
每个端点自带 example_request → 新增模块无需改本文件、零冲突，
天然支持并行子代理各写各模块后自动被覆盖。
"""
import os
import sys
import traceback

# 让 import 能找到 src 下的模块
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))

from contract_runtime import validate_payload
from event_bus import EventBus, build_payment_status_event
from stubs import API_STUB


def _check(name: str, cond: bool):
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}")
    if not cond:
        raise AssertionError(name)


def test_contract_runtime():
    print("· contract_runtime")
    ok, _ = validate_payload("auth-login.request.schema.json",
                             {"channel": "email", "deviceId": "dev-001",
                              "email": "user@x.com", "password": "secret123"})
    _check("合法登录请求通过", ok is True)

    bad, err = validate_payload("auth-login.request.schema.json",
                                {"channel": "email", "deviceId": "dev-001",
                                 "foo": "bar"})
    _check("非法登录请求被拒", bad is False and len(err) > 0)


def test_event_bus():
    print("· event_bus")
    bus = EventBus()
    got = []
    bus.subscribe("payment.status.changed", lambda p: got.append(p))

    ok, msg = bus.publish(build_payment_status_event("O1", "U1", "paid", 29900))
    _check("合法支付事件发布成功", ok is True and len(got) == 1)

    ok2, msg2 = bus.publish(build_payment_status_event("O2", "U1", "paid", -1))
    _check("非法支付事件被拒(fail-closed)", ok2 is False and len(got) == 1)


def test_api_stub_registry():
    print("· api_stub 注册表（自动遍历所有端点）")
    ids = API_STUB.endpoint_ids()
    _check("注册表非空", len(ids) > 0)
    # 已知已落地 8 端点（Auth/Jobs/User/Resume）—— 回归保护
    _expected = {"A01 auth-login", "A02 auth-refresh", "A07 jobs-search",
                 "A08 jobs-favorite", "A03 users-me", "A04 resumes-create",
                 "A05 resumes-versions", "A06 resumes-ats"}
    _check("含已落地 8 端点", _expected.issubset(set(ids)))
    # 每个端点用自带 example_request 应返回 200 + dict 响应
    for ep in API_STUB.endpoints():
        code, body = API_STUB.dispatch_id(ep.name, ep.example_request)
        _check(f"{ep.name} 示例请求 200 + 响应为 dict",
               code == 200 and isinstance(body, dict))
    # 未注册端点 -> 404
    code_x, _ = API_STUB.dispatch_id("ZZZ-unknown", {})
    _check("未注册端点 -> 404", code_x == 404)


def test_api_stub_fail_closed():
    print("· api_stub fail-closed 抽样")
    c1, _ = API_STUB.dispatch_id("A01 auth-login",
                                 {"channel": "email", "deviceId": "dev-001", "foo": "bar"})
    _check("A01 含未声明字段 -> 422", c1 == 422)
    c2, _ = API_STUB.dispatch_id("A07 jobs-search", {"foo": "bar"})
    _check("A07 缺 page/pageSize + 额外字段 -> 422", c2 == 422)
    c3, _ = API_STUB.dispatch_id("A08 jobs-favorite", {"action": "bad"})
    _check("A08 枚举外 action -> 422", c3 == 422)
    c4, _ = API_STUB.dispatch_id("A04 resumes-create", {"foo": "bar"})
    _check("A04 缺 title/content -> 422", c4 == 422)
    # 无请求体端点：空请求也应 200（跳过入参校验）
    c5, _ = API_STUB.dispatch_id("A03 users-me", {})
    _check("A03 无请求体 -> 200", c5 == 200)
    c6, _ = API_STUB.dispatch_id("A05 resumes-versions", {})
    _check("A05 无请求体 -> 200", c6 == 200)


def main():
    print("=== scaffold 冒烟测试 ===")
    try:
        test_contract_runtime()
        test_event_bus()
        test_api_stub_registry()
        test_api_stub_fail_closed()
    except AssertionError as e:
        print(f"\n冒烟测试失败：{e}")
        traceback.print_exc()
        sys.exit(1)
    print(f"\n全部冒烟测试通过 ✅ （共 {len(API_STUB.endpoint_ids())} 端点）")


if __name__ == "__main__":
    main()
