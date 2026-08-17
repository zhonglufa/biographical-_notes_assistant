"""stubs/resume.py — Resume 模块（A04 创建 / A05 版本列表 / A06 ATS）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实写库/ATS 业务逻辑。
"""
from .core import Endpoint


def _resumes_create_handler(req: dict) -> dict:
    return {
        "resumeId": "R-demo-001",
        "versionId": "RV-demo-001",
        "createdAt": 1760000000000,
    }


def _resume_versions_handler(req: dict) -> dict:
    return {
        "versions": [
            {
                "versionId": "RV-demo-001",
                "versionNo": 1,
                "createdAt": 1760000000000,
                "note": "初始版本",
                "isPreferred": True,
            }
        ],
        "diffAvailable": False,
    }


def _resume_ats_handler(req: dict) -> dict:
    return {
        "taskId": "T-ats-demo-001",
        "status": "pending",
    }


ENDPOINTS = [
    Endpoint(
        name="A04 resumes-create",
        request_schema="resumes-create.request.schema.json",
        response_schema="resumes-create.response.schema.json",
        handler=_resumes_create_handler,
        example_request={"title": "Java 工程师简历",
                         "content": {"sections": {}}, "templateId": "tpl-01"},
    ),
    Endpoint(
        name="A05 resumes-versions",
        request_schema=None,  # GET /resumes/{id}/versions 无请求体
        response_schema="resume-versions.response.schema.json",
        handler=_resume_versions_handler,
        example_request={},
    ),
    Endpoint(
        name="A06 resumes-ats",
        request_schema="resume-ats.request.schema.json",
        response_schema="resume-ats.response.schema.json",
        handler=_resume_ats_handler,
        example_request={"resumeVersionId": "RV-demo-001"},
    ),
]
