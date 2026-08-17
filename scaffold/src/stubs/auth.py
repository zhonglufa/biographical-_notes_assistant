"""stubs/auth.py — Auth 模块（A01 登录 / A02 刷新令牌）demo 桩

⚠️ 安全边界（REVIEW-3 红线规避）：handler 均为 demo / mock 桩，
只返回符合响应契约结构的占位数据，不实现任何真实业务逻辑
（不含密码校验、令牌签发/签名、凭据存储、会话策略）。
"""
from .core import Endpoint


def _login_handler(req: dict) -> dict:
    return {
        "accessToken": "demo-access-token",
        "refreshToken": "demo-refresh-token",
        "expiresIn": 3600,
        "userId": "U-demo",
        "plan": "free",
    }


def _refresh_handler(req: dict) -> dict:
    return {
        "accessToken": "demo-access-token-renewed",
        "expiresIn": 3600,
        "refreshToken": None,
    }


ENDPOINTS = [
    Endpoint(
        name="A01 auth-login",
        request_schema="auth-login.request.schema.json",
        response_schema="auth-login.response.schema.json",
        handler=_login_handler,
        example_request={"channel": "email", "deviceId": "dev-001",
                         "email": "user@x.com", "password": "secret123"},
    ),
    Endpoint(
        name="A02 auth-refresh",
        request_schema="auth-refresh.request.schema.json",
        response_schema="auth-refresh.response.schema.json",
        handler=_refresh_handler,
        example_request={"refreshToken": "rt-demo"},
    ),
]
