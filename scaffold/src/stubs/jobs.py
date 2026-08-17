"""stubs/jobs.py — Jobs 模块（A07 岗位搜索 / A08 收藏忽略）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实查询/写库业务逻辑。
"""
from .core import Endpoint


def _jobs_search_handler(req: dict) -> dict:
    return {
        "items": [
            {
                "jobId": "J-demo-001",
                "title": "Java 开发工程师",
                "company": "示例科技有限公司",
                "platformId": "boss-1001",
                "salaryMin": 15000,
                "salaryMax": 25000,
                "location": "深圳",
                "source": "search",
                "matchScore": 88,
                "matchBand": "green",
                "matchReason": "技能匹配度高",
                "favorited": False,
                "collectedAt": 1760000000000,
            }
        ],
        "total": 1,
        "page": req.get("page", 1),
        "pageSize": req.get("pageSize", 20),
    }


def _jobs_favorite_handler(req: dict) -> dict:
    action = req.get("action")
    if action == "favorite":
        return {"ok": True, "favoriteId": "F-demo-001", "status": "favorited"}
    return {"ok": True, "favoriteId": None, "status": "ignored"}


ENDPOINTS = [
    Endpoint(
        name="A07 jobs-search",
        request_schema="jobs-search.request.schema.json",
        response_schema="jobs-list.response.schema.json",
        handler=_jobs_search_handler,
        example_request={"page": 1, "pageSize": 20, "keyword": "Java"},
    ),
    Endpoint(
        name="A08 jobs-favorite",
        request_schema="jobs-favorite.request.schema.json",
        response_schema="jobs-favorite.response.schema.json",
        handler=_jobs_favorite_handler,
        example_request={"action": "favorite"},
    ),
]
