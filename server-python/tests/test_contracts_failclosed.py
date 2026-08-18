"""test_contracts_failclosed.py — fail-closed：HTTP 响应不得偏离机器可读 schema

每个 B 端点成功响应、错误信封、B07 任务状态都过 design/contracts 零依赖校验器。
这是「契约是真相源、实现零偏离」的硬保证（项目双闸门精神在 Python 侧的落地）。
"""
from app.contracts import validate_payload

from helpers import AUTH


def _ok(schema, payload):
    ok, err = validate_payload(schema, payload)
    return ok, err


def test_b01_response_schema(client):
    r = client.post("/internal/v1/ai/match", json={"jd": "java 后端", "resume": "java 后端 5 年"},
                    headers=AUTH)
    assert r.status_code == 200
    ok, err = _ok("b01-match.response.schema.json", r.json())
    assert ok, err


def test_b02_response_schema(client):
    r = client.post("/internal/v1/ai/questions",
                    json={"jd": "java", "resume": "java", "count": 3, "lang": "zh"}, headers=AUTH)
    assert r.status_code == 200
    ok, err = _ok("b02-questions.response.schema.json", r.json())
    assert ok, err


def test_b03_response_schema(client):
    r = client.post("/internal/v1/ai/evaluate",
                    json={"questionId": "q1", "answer": "我会用缓存优化性能，QPS 提升 3 倍。"},
                    headers=AUTH)
    assert r.status_code == 200
    ok, err = _ok("b03-evaluate.response.schema.json", r.json())
    assert ok, err


def test_b04_response_schema(client):
    r = client.post("/internal/v1/ai/resume/optimize",
                    json={"resume": "简历内容", "target": "后端工程师"}, headers=AUTH)
    assert r.status_code == 200
    ok, err = _ok("b04-optimize.response.schema.json", r.json())
    assert ok, err


def test_b05_response_schema(client):
    r = client.post("/internal/v1/ai/ats", json={"resume": "简历简历简历"}, headers=AUTH)
    assert r.status_code == 200
    ok, err = _ok("b05-ats.response.schema.json", r.json())
    assert ok, err


def test_invalid_request_error_envelope(client):
    # 缺 resume（必填）→ 400 INVALID_PARAM，信封须符合 error-envelope.schema.json
    r = client.post("/internal/v1/ai/match", json={"jd": "x"}, headers=AUTH)
    assert r.status_code == 400
    body = r.json()
    ok, err = _ok("error-envelope.schema.json", body)
    assert ok, err
    assert body["code"] == "INVALID_PARAM"
    assert body["retryable"] is False
    assert "traceId" in body


def test_unauthorized_error_envelope(client):
    r = client.post("/internal/v1/ai/match", json={"jd": "x", "resume": "y"})
    assert r.status_code == 401
    body = r.json()
    ok, err = _ok("error-envelope.schema.json", body)
    assert ok, err
    assert body["code"] == "UNAUTHORIZED"


def test_b07_task_status_schema(client):
    r = client.post("/internal/v1/agent/jobs/search",
                    json={"taskId": "t1", "platformId": "boss", "query": "java"},
                    headers=AUTH)
    assert r.status_code == 200
    ok, err = _ok("b07-task-result.schema.json", r.json())
    assert ok, err
    # 任务状态可经 B07 查询接口再次返回且合规
    r2 = client.get("/internal/v1/agent/tasks/t1", headers=AUTH)
    assert r2.status_code == 200
    ok2, err2 = _ok("b07-task-result.schema.json", r2.json())
    assert ok2, err2
