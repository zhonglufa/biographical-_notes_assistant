"""stubs/interview.py — Interview 模块（A16 题库 / A17 建会话 / A18 作答 / A19 报告）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实 LLM 面试业务逻辑。
"""
from .core import Endpoint


def _interview_questions_handler(req: dict) -> dict:
    return {
        "questionSets": [
            {
                "setId": "qs-demo-001",
                "title": "Java 基础题库",
                "questionCount": 10,
            }
        ]
    }


def _interview_session_create_handler(req: dict) -> dict:
    return {
        "sessionId": "SES-demo-001",
        "status": "created",
    }


def _interview_session_answer_handler(req: dict) -> dict:
    return {"accepted": True}


def _interview_session_report_handler(req: dict) -> dict:
    return {
        "sessionId": "SES-demo-001",
        "overallScore": 80,
        "dimensions": [
            {"dim": "communication", "rawScore": 4, "reason": "表达清晰"}
        ],
        "feedback": "整体表现良好，建议加强系统设计。",
    }


ENDPOINTS = [
    Endpoint(
        name="A16 interview-questions",
        request_schema=None,   # GET 无请求体
        response_schema="interview-questions.response.schema.json",
        handler=_interview_questions_handler,
        example_request={},
    ),
    Endpoint(
        name="A17 interview-session-create",
        request_schema="interview-session-create.request.schema.json",
        response_schema="interview-session-create.response.schema.json",
        handler=_interview_session_create_handler,
        example_request={"mode": "text", "jobId": None, "questionSetId": None},
    ),
    Endpoint(
        name="A18 interview-session-answer",
        request_schema="interview-session-answer.request.schema.json",
        response_schema="interview-session-answer.response.schema.json",
        handler=_interview_session_answer_handler,
        example_request={"questionId": "q-demo-001", "answer": "我的回答要点...",
                         "asrProvider": None},
    ),
    Endpoint(
        name="A19 interview-session-report",
        request_schema=None,   # GET 无请求体
        response_schema="interview-session-report.response.schema.json",
        handler=_interview_session_report_handler,
        example_request={},
    ),
]
