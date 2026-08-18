"""test_agent_trigger.py — B10/B11 触发受理 + B07 状态 + B09 健康（均需鉴权）"""
from helpers import AUTH


def test_b10_search_accept_and_status(client):
    r = client.post("/internal/v1/agent/jobs/search",
                    json={"taskId": "t1", "platformId": "boss", "query": "java", "page": 1},
                    headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert b["taskId"] == "t1" and b["status"] == "pending"
    # B07 状态可再查
    r2 = client.get("/internal/v1/agent/tasks/t1", headers=AUTH)
    assert r2.status_code == 200 and r2.json()["taskId"] == "t1"


def test_b11_detail(client):
    r = client.post("/internal/v1/agent/jobs/detail",
                    json={"taskId": "t2", "platformId": "lagou", "externalJobId": "job-9"},
                    headers=AUTH)
    assert r.status_code == 200
    assert r.json()["status"] == "pending"


def test_b09_health_report_and_query(client):
    r = client.post("/internal/v1/agent/health",
                    json={"platformId": "boss", "healthy": True,
                          "metrics": {"domParseSuccessRate": 0.99, "avgLatencyMs": 120,
                                      "cookieHealthy": True},
                          "checkedAt": 123},
                    headers=AUTH)
    assert r.status_code == 200
    r2 = client.get("/internal/v1/agent/health/boss", headers=AUTH)
    assert r2.status_code == 200 and r2.json()["healthy"] is True


def test_b09_missing_metrics_rejected(client):
    r = client.post("/internal/v1/agent/health",
                    json={"platformId": "boss", "healthy": False, "checkedAt": 1}, headers=AUTH)
    assert r.status_code == 400  # metrics 必填（additionalProperties:false）


def test_agent_requires_auth(client):
    r = client.post("/internal/v1/agent/jobs/search",
                    json={"taskId": "x", "platformId": "boss", "query": "java"})
    assert r.status_code == 401


def test_task_not_found(client):
    r = client.get("/internal/v1/agent/tasks/nope", headers=AUTH)
    assert r.status_code == 404
    assert r.json()["code"] == "RESOURCE_NOT_FOUND"
