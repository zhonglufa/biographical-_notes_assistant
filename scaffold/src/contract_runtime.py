"""
contract_runtime.py — 契约优先运行期加载/校验（B3 增强版）

职责：让代码在运行时复用 design/contracts/ 的机器可读契约（schema 66 / 注册表 6），
      对任意请求/响应/事件 payload 做「契约校验」，确保实现不偏离设计基线。

设计哲学（contract-first）：
  设计文档里的 *.schema.json 是「唯一真相源」；代码只是契约的执行者。
  每次接口入参/出参、每次事件发布前，都先过一遍 validate()，失败即 fail-closed。

依赖：纯标准库 + 复用 design/contracts/validate_contracts.py 的 validate()（零外部依赖）。

B3 增强点（2026-08-17）：
  - ContractRuntime：包裹 API_STUB 注册表，提供 call() 归一化结果 + 错误码映射；
  - ERROR_CODES：从 error-codes.json 加载，支持按内部错误键映射到规范错误码；
  - validate_all_examples()：跑通全部注册端点的 example_request（测试基座复用）。
"""
import json
import os
import sys
from dataclasses import dataclass

# 把 design/contracts 加入搜索路径，复用既有零依赖校验器（不重复造轮子）
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONTRACTS_DIR = os.path.join(_REPO_ROOT, "design", "contracts")
sys.path.insert(0, _CONTRACTS_DIR)

import validate_contracts  # 复用其内部 validate() 函数


# ---------------------------------------------------------------------------
# 基础：加载 + 校验
# ---------------------------------------------------------------------------
def load_schema(schema_name: str) -> dict:
    """按文件名加载一个 JSON Schema。

    schema_name: 例如 "auth-login.request.schema.json"
    返回：解析后的 dict（schema 对象）
    """
    path = os.path.join(_CONTRACTS_DIR, schema_name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_payload(schema_name: str, payload) -> tuple:
    """对 payload 用指定 schema 做校验。

    返回 (是否通过, 错误信息)。错误信息为空串表示通过。
    复用 validate_contracts.validate —— 失败时抛 SchemaError，这里包成布尔。
    """
    schema = load_schema(schema_name)
    try:
        validate_contracts.validate(payload, schema)
        return True, ""
    except validate_contracts.SchemaError as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# 错误码表（B3）：从 error-codes.json 加载
# ---------------------------------------------------------------------------
def _load_error_codes() -> dict:
    path = os.path.join(_CONTRACTS_DIR, "error-codes.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {e["code"]: e for e in data["registry"]}


ERROR_CODES = _load_error_codes()

# 内部错误键（Endpoint.dispatch 产生的 error 字段）-> 规范错误码
_INTERNAL_ERROR_MAP = {
    "unknown_endpoint": "RESOURCE_NOT_FOUND",
    "request_schema_violation": "INVALID_PARAM",
    # response_schema_violation 是「实现偏离契约」的内部 500，无对应公开错误码，
    # 不编造未登记码，交由 ContractResult.contract_breach 标记暴露。
}


# ---------------------------------------------------------------------------
# 归一化调用结果（B3）
# ---------------------------------------------------------------------------
@dataclass
class ContractResult:
    status: int          # HTTP 状态码（200 / 404 / 422 / 500 ...）
    body: dict           # 响应体
    error_code: str | None = None   # 映射到的规范错误码（None=非规范/内部）
    contract_breach: bool = False   # 响应契约被破坏（实现 bug，500）
    ok: bool = True      # status == 200

    def __post_init__(self):
        if self.ok is True and self.status != 200:
            self.ok = (self.status == 200)


class ContractRuntime:
    """契约优先运行期：包裹 API_STUB 注册表，提供归一化 call() + 错误码映射。

    生产环境 HTTP 层可调用本类；测试基座/冒烟均可直接复用。
    不自动注册新端点（保持双闸门 + 冒烟 25/25 不变）。
    """

    def call(self, endpoint_id: str, request: dict | None = None) -> ContractResult:
        """调用一个端点，返回归一化 ContractResult。

        - 未知端点   -> 404 + error_code=RESOURCE_NOT_FOUND
        - 入参违规   -> 422 + error_code=INVALID_PARAM
        - 响应违规   -> 500 + contract_breach=True（实现偏离契约，暴露而非吞掉）
        - 正常       -> 200 + body
        """
        # 惰性 import，避免与 stubs 包的循环依赖（stubs 启动时会 import 本模块）
        from stubs import API_STUB

        req = request if request is not None else {}
        status, body = API_STUB.dispatch_id(endpoint_id, req)

        error_code = None
        contract_breach = False
        if status == 404 and isinstance(body, dict) and body.get("error") == "unknown_endpoint":
            error_code = _INTERNAL_ERROR_MAP["unknown_endpoint"]
        elif status == 422 and isinstance(body, dict) and body.get("error") == "request_schema_violation":
            error_code = _INTERNAL_ERROR_MAP["request_schema_violation"]
        elif status == 500 and isinstance(body, dict) and body.get("error") == "response_schema_violation":
            contract_breach = True

        return ContractResult(status=status, body=body if isinstance(body, dict) else {},
                              error_code=error_code, contract_breach=contract_breach,
                              ok=(status == 200))

    def list_endpoints(self) -> list:
        """列出全部已注册端点 id。"""
        from stubs import API_STUB
        return API_STUB.endpoint_ids()

    def validate_all_examples(self) -> dict:
        """跑通全部注册端点的 example_request，返回 {endpoint_id: ContractResult}。

        测试基座核心：一次遍历确认「所有端点示例请求都能被契约放行且返回 200」。
        """
        from stubs import API_STUB
        out = {}
        for ep in API_STUB.endpoints():
            out[ep.name] = self.call(ep.name, ep.example_request)
        return out


def error_code_info(code: str) -> dict | None:
    """按规范错误码查详情（http/retryable/namespace/user_action）。"""
    return ERROR_CODES.get(code)


if __name__ == "__main__":
    # 自测：校验合法/非法登录请求 + 归一化调用 + 错误码映射
    ok, err = validate_payload("auth-login.request.schema.json",
                                {"channel": "email", "deviceId": "dev-001",
                                 "email": "user@x.com", "password": "secret123"})
    print("合法登录请求 ->", "通过" if ok else f"失败: {err}")

    bad, err2 = validate_payload("auth-login.request.schema.json",
                                  {"channel": "email", "deviceId": "dev-001",
                                   "foo": "bar"})  # 含 additionalProperties:false 禁止的额外字段
    print("非法登录请求 ->", "通过(异常!)" if bad else f"正确拒绝: {err2}")

    rt = ContractRuntime()
    r1 = rt.call("A01 auth-login", {"channel": "email", "deviceId": "dev-001",
                                    "email": "user@x.com", "password": "secret123"})
    print(f"call A01 合法 -> status={r1.status} ok={r1.ok}")
    r2 = rt.call("A01 auth-login", {"channel": "email", "deviceId": "dev-001", "foo": "bar"})
    print(f"call A01 非法 -> status={r2.status} error_code={r2.error_code}")
    r3 = rt.call("ZZZ-unknown", {})
    print(f"call 未知端点 -> status={r3.status} error_code={r3.error_code}")
    print(f"错误码表规模: {len(ERROR_CODES)} 条")
