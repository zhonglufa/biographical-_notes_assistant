"""stubs/user.py — User 模块（A03 当前用户与权益）demo 桩（无请求体 GET）

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实查询/权限判定业务逻辑。
"""
from .core import Endpoint


def _user_me_handler(req: dict) -> dict:
    return {
        "userId": "U-demo",
        "email": "user@x.com",
        "plan": "free",
        "quotaUsed": 0,
        "quotaLimit": 100,
        "preferences": {"pushTime": "09:00", "doNotDisturb": False},
    }


ENDPOINTS = [
    Endpoint(
        name="A03 users-me",
        request_schema=None,  # GET /users/me 无请求体
        response_schema="user-me.response.schema.json",
        handler=_user_me_handler,
        example_request={},
    ),
]
