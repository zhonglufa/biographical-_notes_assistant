"""
api_stub.py — 契约优先的接口分发骨架（D 阶段奠基切片）

演示「请求入参 + 响应出参 都必须过契约校验」的 contract-first 模式。
这是一个传输无关的「端点」抽象：生产环境把它挂到 FastAPI/Flask/本机 Agent 的
HTTP 层即可，但「校验规则」与这里完全一致 —— 换 Web 框架不改契约逻辑。

本切片已落地 **Auth 模块 (A01 登录 + A02 刷新令牌)** 两个端点，证明模块级
contract-first 落地模式可行；后续 A 层端点按同模式逐一对齐 schema 即可
（见 README §3 脚手架顺序）。每个端点都是一个 `Endpoint` 实例，统一由
`API_STUB` 注册表按 id 分发。

⚠️ 安全边界（REVIEW-3 红线规避）：本文件所有 handler 均为 **demo / mock 桩**，
只返回符合响应契约结构的占位数据（占位令牌），**不实现任何真实鉴权逻辑**
（不含密码校验、令牌签发/签名、凭据存储、会话策略）。真实鉴权在 B 阶段由
服务端 security 模块实现，本脚手架仅演示「契约校验」机制本身。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contract_runtime import validate_payload


class Endpoint:
    """一个契约优先的端点：请求/响应均先校验，再执行 handler。"""

    def __init__(self, name: str, request_schema: str, response_schema: str, handler):
        self.name = name
        self.request_schema = request_schema
        self.response_schema = response_schema
        self._handler = handler

    def dispatch(self, request: dict) -> tuple[int, dict]:
        """分发一次调用。

        返回 (HTTP 状态码, body)。
          - 请求不合规 -> 422（fail-closed，绝不执行业务）
          - 响应不合规 -> 500（实现偏离契约，暴露而非吞掉）
          - 正常        -> 200 + handler 结果
        """
        ok, err = validate_payload(self.request_schema, request)
        if not ok:
            return 422, {"error": "request_schema_violation", "detail": err}

        resp = self._handler(request)

        ok2, err2 = validate_payload(self.response_schema, resp)
        if not ok2:
            return 500, {"error": "response_schema_violation", "detail": err2}
        return 200, resp


class ApiStub:
    """端点注册表 + 按 id 分发。生产环境可挂 HTTP 层，此处仅演示契约校验。"""

    def __init__(self):
        self._endpoints = {}

    def register(self, endpoint: Endpoint) -> Endpoint:
        self._endpoints[endpoint.name] = endpoint
        return endpoint

    def dispatch_id(self, endpoint_id: str, request: dict) -> tuple[int, dict]:
        ep = self._endpoints.get(endpoint_id)
        if ep is None:
            return 404, {"error": "unknown_endpoint", "endpoint": endpoint_id}
        return ep.dispatch(request)

    def endpoint_ids(self) -> list[str]:
        return list(self._endpoints.keys())


# ---- Auth 模块 demo 桩（仅演示契约，不含真实鉴权）----

def _login_handler(req: dict) -> dict:
    # 真实实现会校验密码 + 派发令牌；此处只回一个符合响应契约的结构
    # （响应契约要求 accessToken/refreshToken/expiresIn/userId/plan，且 additionalProperties:false）
    return {
        "accessToken": "demo-access-token",
        "refreshToken": "demo-refresh-token",
        "expiresIn": 3600,
        "userId": "U-demo",
        "plan": "free",
    }


def _refresh_handler(req: dict) -> dict:
    # 真实实现会用 refreshToken 换发新 accessToken，并视策略轮转 refreshToken；
    # 此处只回符合响应契约的占位结构（refreshToken 未轮转时可为 null）
    return {
        "accessToken": "demo-access-token-renewed",
        "expiresIn": 3600,
        "refreshToken": None,
    }


AUTH_LOGIN = Endpoint(
    name="A01 auth-login",
    request_schema="auth-login.request.schema.json",
    response_schema="auth-login.response.schema.json",
    handler=_login_handler,
)

AUTH_REFRESH = Endpoint(
    name="A02 auth-refresh",
    request_schema="auth-refresh.request.schema.json",
    response_schema="auth-refresh.response.schema.json",
    handler=_refresh_handler,
)

# 全局注册表：已落地 Auth 模块（A01/A02），后续端点按同模式注册即可。
API_STUB = ApiStub()
API_STUB.register(AUTH_LOGIN)
API_STUB.register(AUTH_REFRESH)


if __name__ == "__main__":
    code, body = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                       "email": "user@x.com", "password": "secret123"})
    print("合法登录 ->", code, body)

    code2, body2 = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                         "foo": "bar"})  # 含禁止额外字段
    print("非法登录 ->", code2, body2)

    code3, body3 = API_STUB.dispatch_id("A02 auth-refresh", {"refreshToken": "rt-abc"})
    print("合法刷新 ->", code3, body3)

    code4, body4 = API_STUB.dispatch_id("A02 auth-refresh", {})  # 缺 refreshToken
    print("非法刷新 ->", code4, body4)
