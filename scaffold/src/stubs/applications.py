"""stubs/applications.py — Applications 模块（A09 批量投递 / A10 列表 / A11 详情）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实批量投递 / 写库业务逻辑。
A09 / A11 暂无严格 schema（ref HLD §4.2 / §4.3）→ request/response schema 均为 None（不伪造契约）。
"""
from .core import Endpoint


def _applications_batch_handler(req: dict) -> dict:
    # A09：响应 schema 待补（HLD §4.2），桩侧返回占位确认（不实现真实批量投递）
    return {"accepted": 0, "rejected": 0, "taskId": "batch-demo-001"}


def _applications_list_handler(req: dict) -> dict:
    return {
        "items": [
            {
                "applicationId": "APP-demo-001",
                "jobId": "JOB-demo-001",
                "platformId": "boss",
                "status": "submitted",
                "appliedAt": 1760000000000,
            }
        ],
        "total": 1,
    }


def _applications_detail_handler(req: dict) -> dict:
    # A11：响应 schema 待补（HLD §4.3），桩侧返回占位
    return {"applicationId": "APP-demo-001", "status": "applied"}


ENDPOINTS = [
    Endpoint(
        name="A09 applications-batch",
        request_schema=None,   # ref HLD §4.2，严格 schema 待补（不伪造契约）
        response_schema=None,  # ref HLD §4.2，严格 schema 待补（不伪造契约）
        handler=_applications_batch_handler,
        example_request={},
    ),
    Endpoint(
        name="A10 applications-list",
        request_schema=None,   # GET 无请求体
        response_schema="applications-list.response.schema.json",
        handler=_applications_list_handler,
        example_request={},
    ),
    Endpoint(
        name="A11 applications-detail",
        request_schema=None,   # ref HLD §4.3，严格 schema 待补（不伪造契约）
        response_schema=None,  # ref HLD §4.3，严格 schema 待补（不伪造契约）
        handler=_applications_detail_handler,
        example_request={},
    ),
]
