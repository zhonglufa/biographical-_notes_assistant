"""test_b05_ats.py — B05 ATS 评分（降级启发式 + 主链路 + 事件）"""
from helpers import AUTH


def test_b05_degrade_heuristic(client):
    r = client.post("/internal/v1/ai/ats",
                    json={"resume": "教育背景 工作经历 项目经历 技能特长 实习经历"},
                    headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert 0.0 <= b["atsScore"] <= 100.0
    assert isinstance(b["suggestions"], list) and len(b["suggestions"]) >= 1


def test_b05_primary_publishes_event(primary):
    c, orch = primary
    r = c.post("/internal/v1/ai/ats", json={"resume": "简历"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["atsScore"] == 82.5
    assert len(orch.publisher.events) == 1
    ev = orch.publisher.events[0]
    assert ev["method"] == "b05" and ev["status"] == "ok"
