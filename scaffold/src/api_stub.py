"""
api_stub.py — 契约优先的接口分发骨架（D 阶段奠基切片）

演示「请求入参 + 响应出参 都必须过契约校验」的 contract-first 模式。
这是一个传输无关的「端点」抽象：生产环境把它挂到 FastAPI/Flask/本机 Agent 的
HTTP 层即可，但「校验规则」与这里完全一致 —— 换 Web 框架不改契约逻辑。

本切片只落地一个示例端点 auth-login（A01），证明模式可行；后续 24 个 A 端点
按同模式逐一对齐 schema 即可（见 README §3 脚手架顺序）。
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


# ---- 示例端点 A01 登录：仅做契约演示，不含真实鉴权 ----
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


AUTH_LOGIN = Endpoint(
    name="A01 auth-login",
    request_schema="auth-login.request.schema.json",
    response_schema="auth-login.response.schema.json",
    handler=_login_handler,
)


if __name__ == "__main__":
    code, body = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                       "email": "user@x.com", "password": "secret123"})
    print("合法登录 ->", code, body)

    code2, body2 = AUTH_LOGIN.dispatch({"channel": "email", "deviceId": "dev-001",
                                         "foo": "bar"})  # 含禁止额外字段
    print("非法登录 ->", code2, body2)
