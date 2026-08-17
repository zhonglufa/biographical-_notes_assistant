"""stubs/adapters.py — Adapters 模块（A14 列表 / A15 启用）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实适配器调度业务逻辑。
A14 暂无严格 schema（ref HLD §4.4）→ request/response schema 均为 None（不伪造契约）。
"""
from .core import Endpoint


def _adapters_list_handler(req: dict) -> dict:
    # A14：响应 schema 待补（HLD §4.4），桩侧返回占位
    return {"adapters": [], "count": 0}


def _adapter_enable_handler(req: dict) -> dict:
    enabled = req.get("enabled", True)
    return {
        "adapterId": "adp-demo-001",
        "status": "enabled" if enabled else "disabled",
    }


ENDPOINTS = [
    Endpoint(
        name="A14 adapters-list",
        request_schema=None,   # ref HLD §4.4，严格 schema 待补（不伪造契约）
        response_schema=None,  # ref HLD §4.4，严格 schema 待补（不伪造契约）
        handler=_adapters_list_handler,
        example_request={},
    ),
    Endpoint(
        name="A15 adapter-enable",
        request_schema="adapter-enable.request.schema.json",
        response_schema="adapter-enable.response.schema.json",
        handler=_adapter_enable_handler,
        example_request={"enabled": True},
    ),
]
