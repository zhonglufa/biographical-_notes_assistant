"""test_contract_runtime.py — 契约运行期测试（B3）

验证：ContractRuntime.call() 归一化结果 + 错误码映射 + 全端点示例请求过契约。
零外部依赖，直接 `python scaffold/tests/test_contract_runtime.py` 运行。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from base import check
from contract_runtime import ContractRuntime, validate_payload, error_code_info, ERROR_CODES


def test_call_ok():
    print("· ContractRuntime.call 合法路径")
    rt = ContractRuntime()
    r = rt.call("A01 auth-login", {"channel": "email", "deviceId": "dev-001",
                                   "email": "user@x.com", "password": "secret123"})
    check("A01 合法请求 -> 200 + ok", r.status == 200 and r.ok is True)
    check("A01 响应体为 dict", isinstance(r.body, dict))
    check("A01 无错误码", r.error_code is None)


def test_call_unknown_endpoint():
    print("· 未知端点 -> 404 + 规范错误码")
    rt = ContractRuntime()
    r = rt.call("ZZZ-unknown", {})
    check("未知端点 -> 404", r.status == 404)
    check("未知端点 error_code=RESOURCE_NOT_FOUND", r.error_code == "RESOURCE_NOT_FOUND")
    info = error_code_info("RESOURCE_NOT_FOUND")
    check("RESOURCE_NOT_FOUND 在错误码表且 http=404", info is not None and info["http"] == 404)


def test_call_bad_request():
    print("· 入参违规 -> 422 + 规范错误码")
    rt = ContractRuntime()
    r = rt.call("A01 auth-login", {"channel": "email", "deviceId": "dev-001", "foo": "bar"})
    check("非法请求 -> 422", r.status == 422)
    check("非法请求 error_code=INVALID_PARAM", r.error_code == "INVALID_PARAM")
    info = error_code_info("INVALID_PARAM")
    check("INVALID_PARAM http=400", info is not None and info["http"] == 400)


def test_validate_all_examples():
    print("· validate_all_examples 遍历全部注册端点")
    rt = ContractRuntime()
    res = rt.validate_all_examples()
    check("遍历结果非空", len(res) > 0)
    bad = [eid for eid, r in res.items() if r.status != 200]
    check(f"全部端点示例请求 -> 200（实际 {len(res)-len(bad)}/{len(res)}）", not bad)


def main():
    print("=== test_contract_runtime ===")
    test_call_ok()
    test_call_unknown_endpoint()
    test_call_bad_request()
    test_validate_all_examples()
    rt = ContractRuntime()
    print(f"契约运行期测试通过 ✅（端点 {len(rt.list_endpoints())} 个，错误码 {len(ERROR_CODES)} 条）")


if __name__ == "__main__":
    main()
