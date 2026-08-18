"""stubs/strategies.py — Strategies 模块（A12 查 / A13 改）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实策略持久化业务逻辑。
"""
from .core import Endpoint


def _strategies_get_handler(req: dict) -> dict:
    return {
        "matchThreshold": 0.7,
        "dailyLimit": 20,
        "platforms": ["boss", "lagou"],
        "blacklist": ["spam-corp"],
    }


def _strategies_update_handler(req: dict) -> dict:
    # 回显请求中的关键字段，符合 strategies.response 结构
    return {
        "matchThreshold": req.get("matchThreshold", 0.7),
        "dailyLimit": req.get("dailyLimit", 20),
        "platforms": req.get("platforms", []),
        "blacklist": req.get("blacklist", []),
    }


ENDPOINTS = [
    Endpoint(
        name="A12 strategies-get",
        request_schema=None,   # GET 无请求体
        response_schema="strategies.response.schema.json",
        handler=_strategies_get_handler,
        example_request={},
    ),
    Endpoint(
        name="A13 strategies-update",
        request_schema="strategies.request.schema.json",
        response_schema="strategies.response.schema.json",
        handler=_strategies_update_handler,
        example_request={"matchThreshold": 0.8, "dailyLimit": 30,
                         "platforms": ["boss"], "blacklist": []},
    ),
]
