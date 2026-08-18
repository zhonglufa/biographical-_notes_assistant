"""test_b02_questions.py — B02 面试题生成（降级题库 + 主链路 + 事件发布）"""
from helpers import AUTH


def test_b02_degrade_bank(client):
    r = client.post("/internal/v1/ai/questions",
                    json={"jd": "java", "resume": "java", "count": 3, "lang": "zh"},
                    headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert len(b["questions"]) == 3
    types = {q["type"] for q in b["questions"]}
    assert types <= {"behavior", "tech", "case"}
    assert all(q["id"] and q["text"] for q in b["questions"])


def test_b02_count_clamped(client):
    # count 超过 20 → 被规则引擎钳制到 20（请求 schema 上限 20，pydantic 已拒 >20；
    # 此处验证边界 20 通过且返回 20 条）
    r = client.post("/internal/v1/ai/questions",
                    json={"jd": "java", "resume": "java", "count": 20, "lang": "zh"},
                    headers=AUTH)
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 20


def test_b02_invalid_count(client):
    r = client.post("/internal/v1/ai/questions",
                    json={"jd": "java", "resume": "java", "count": 99, "lang": "zh"},
                    headers=AUTH)
    assert r.status_code == 400


def test_b02_primary_publishes_event(primary):
    c, orch = primary
    r = c.post("/internal/v1/ai/questions",
               json={"jd": "java", "resume": "java", "count": 2, "lang": "zh"},
               headers=AUTH)
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 3  # FakeLLM 固定返回 3 题
    # 异步结果应经 ai.task.result 事件发布（status=ok）
    assert len(orch.publisher.events) == 1
    ev = orch.publisher.events[0]
    assert ev["method"] == "b02"
    assert ev["status"] == "ok"
