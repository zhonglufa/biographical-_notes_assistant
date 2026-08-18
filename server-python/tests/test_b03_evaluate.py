"""test_b03_evaluate.py — B03 作答评估（降级 advise + 主链路）"""
from helpers import AUTH


def test_b03_degrade_advise(client):
    r = client.post("/internal/v1/ai/evaluate",
                    json={"questionId": "q1",
                          "answer": "我用 Redis 缓存热点数据，把接口 P99 从 800ms 降到 200ms，QPS 提升 3 倍。"},
                    headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert 0.0 <= b["score"] <= 1.0
    assert isinstance(b["rubric"], list) and len(b["rubric"]) >= 1
    assert all("dim" in x and "score" in x for x in b["rubric"])
    assert b["feedback"]


def test_b03_custom_rubric_dims(client):
    r = client.post("/internal/v1/ai/evaluate",
                    json={"questionId": "q2", "answer": "略", "rubricDims": ["技术深度", "表达"]},
                    headers=AUTH)
    assert r.status_code == 200
    dims = {x["dim"] for x in r.json()["rubric"]}
    assert dims == {"技术深度", "表达"}


def test_b03_primary_deepseek(primary):
    c, orch = primary
    r = c.post("/internal/v1/ai/evaluate",
               json={"questionId": "q1", "answer": "回答内容"}, headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert b["score"] == 0.9
    assert b["feedback"] == "回答结构清晰"
