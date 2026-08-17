"""stubs/notifications.py — Notifications 模块（A22 列表 / A23 长连接地址）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实通知推送 / WS 鉴权业务逻辑。
"""
from .core import Endpoint


def _notifications_list_handler(req: dict) -> dict:
    return {
        "items": [
            {
                "id": "NTF-demo-001",
                "level": "L1",
                "title": "投递成功",
                "read": False,
                "createdAt": 1760000000000,
            }
        ],
        "unread": 1,
    }


def _notification_ws_handler(req: dict) -> dict:
    return {
        "wsUrl": "wss://notify.demo.example/ws/NTF-demo-001",
    }


ENDPOINTS = [
    Endpoint(
        name="A22 notifications-list",
        request_schema=None,   # GET 无请求体
        response_schema="notifications-list.response.schema.json",
        handler=_notifications_list_handler,
        example_request={},
    ),
    Endpoint(
        name="A23 notification-ws",
        request_schema=None,   # GET 无请求体
        response_schema="notification-ws.response.schema.json",
        handler=_notification_ws_handler,
        example_request={},
    ),
]
