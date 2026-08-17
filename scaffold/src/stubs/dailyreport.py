"""stubs/dailyreport.py — DailyReport 模块（A24 今日日报 / A25 推送偏好）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实统计聚合 / 推送调度业务逻辑。
"""
from .core import Endpoint


def _daily_report_today_handler(req: dict) -> dict:
    return {
        "date": "2026-08-17",
        "summary": "今日投递 3 个岗位，成功 2 个，收到 1 个面试邀约。",
        "stats": {
            "appliedTotal": 3,
            "success": 2,
            "failed": 1,
            "byPlatform": [
                {"platformId": "boss", "count": 2},
                {"platformId": "lagou", "count": 1},
            ],
            "hrViews": 1,
            "interviewInvites": 1,
            "newQuestions": 5,
            "trend7d": [
                {"date": "2026-08-11", "count": 1},
                {"date": "2026-08-12", "count": 0},
                {"date": "2026-08-13", "count": 2},
                {"date": "2026-08-14", "count": 1},
                {"date": "2026-08-15", "count": 3},
                {"date": "2026-08-16", "count": 2},
                {"date": "2026-08-17", "count": 3},
            ],
        },
    }


def _daily_report_preference_handler(req: dict) -> dict:
    return {
        "ok": True,
        "updatedAt": 1760000000000,
    }


ENDPOINTS = [
    Endpoint(
        name="A24 daily-report-today",
        request_schema=None,   # GET 无请求体
        response_schema="daily-report-today.response.schema.json",
        handler=_daily_report_today_handler,
        example_request={},
    ),
    Endpoint(
        name="A25 daily-report-preference",
        request_schema="daily-report-preference.request.schema.json",
        response_schema="daily-report-preference.response.schema.json",
        handler=_daily_report_preference_handler,
        example_request={"pushTime": "08:00", "enabled": True},
    ),
]
