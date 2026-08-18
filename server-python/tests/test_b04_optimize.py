"""test_b04_optimize.py — B04 简历优化（降级模板 + 主链路 + 事件）"""
from helpers import AUTH


def test_b04_degrade_template(client):
    r = client.post("/internal/v1/ai/resume/optimize",
                    json={"resume": "原始简历", "target": "后端工程师"}, headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert b["optimized"]  # 含原始简历 + 模板占位说明
    assert len(b["changes"]) >= 1
    # 模板兜底明确标注未做语义优化（诚实，不伪造 LLM 结果）
    assert any("模板占位" in c["to"] for c in b["changes"])


def test_b04_primary_publishes_event(primary):
    c, orch = primary
    r = c.post("/internal/v1/ai/resume/optimize",
               json={"resume": "原", "target": "后端"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["optimized"] == "OPT"
    assert len(orch.publisher.events) == 1
    ev = orch.publisher.events[0]
    assert ev["method"] == "b04" and ev["status"] == "ok"
