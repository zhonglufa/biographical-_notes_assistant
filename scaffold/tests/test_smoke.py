"""
test_smoke.py — D 阶段奠基切片冒烟测试（零外部依赖，仅标准库）

验证三件事：
  1) 契约加载/校验可用（contract_runtime）
  2) 事件发布前的契约校验 fail-closed（event_bus）
  3) 接口分发的契约校验 fail-closed（api_stub）

运行：
  cd scaffold && python tests/test_smoke.py
（需 Python 3.10+；复用仓库 design/contracts/ 的零依赖校验器）
"""
import os
import sys
import traceback

# 让 import 能找到 src 下的模块
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))

from contract_runtime import validate_payload
from event_bus import EventBus, build_payment_status_event
from api_stub import AUTH_LOGIN, AUTH_REFRESH, API_STUB


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
                                 "foo": "bar"})  # additionalProperties:false 禁止额外字段
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


def test_api_stub():
    print("· api_stub (Auth 模块 A01/A02)")
    # ---- A01 登录 ----
    code, body = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                       "email": "user@x.com", "password": "secret123"})
    _check("合法登录 200 + 响应合规", code == 200 and body.get("plan") == "free")

    code2, _ = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                     "foo": "bar"})  # 含禁止额外字段
    _check("非法登录 422(fail-closed)", code2 == 422)

    # ---- A02 刷新令牌 ----
    code3, body3 = AUTH_REFRESH.dispatch({"refreshToken": "rt-demo"})
    _check("合法刷新 200 + 响应含新 accessToken",
           code3 == 200 and isinstance(body3.get("accessToken"), str)
           and body3["accessToken"])

    code4, _ = AUTH_REFRESH.dispatch({})  # 缺必需字段 refreshToken
    _check("非法刷新(缺 refreshToken) 422(fail-closed)", code4 == 422)

    # ---- 注册表按 id 分发 ----
    code5, _ = API_STUB.dispatch_id("A01 auth-login",
                                    {"channel": "email", "deviceId": "dev-001",
                                     "email": "user@x.com", "password": "secret123"})
    _check("注册表分发 A01 -> 200", code5 == 200)

    code6, _ = API_STUB.dispatch_id("A02 auth-refresh", {"refreshToken": "rt-demo"})
    _check("注册表分发 A02 -> 200", code6 == 200)

    code7, _ = API_STUB.dispatch_id("ZZZ-unknown", {"x": 1})
    _check("未注册端点 -> 404", code7 == 404)

    _check("注册表含 A01/A02 两端点",
           set(API_STUB.endpoint_ids()) >= {"A01 auth-login", "A02 auth-refresh"})


def main():
    print("=== scaffold 冒烟测试 ===")
    try:
        test_contract_runtime()
        test_event_bus()
        test_api_stub()
    except AssertionError as e:
        print(f"\n冒烟测试失败：{e}")
        traceback.print_exc()
        sys.exit(1)
    print("\n全部冒烟测试通过 ✅")


if __name__ == "__main__":
    main()
