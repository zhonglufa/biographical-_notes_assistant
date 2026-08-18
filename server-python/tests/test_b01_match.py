"""test_b01_match.py — B01 匹配：降级链 + 主链路 + 权重"""
from helpers import AUTH


def test_b01_degrade_rule(client):
    r = client.post("/internal/v1/ai/match",
                    json={"jd": "招聘 java 后端工程师，北京，5 年经验，互联网行业",
                          "resume": "本人 java 后端，北京，6 年经验，互联网公司"},
                    headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert b["model"] == "rule"          # 无 LLM key → 规则引擎兜底
    assert 0.0 <= b["score"] <= 1.0
    assert isinstance(b["matchedSkills"], list)
    assert b["explanation"]


def test_b01_with_weights_degrade(client):
    r = client.post("/internal/v1/ai/match",
                    json={"jd": "java 开发", "resume": "java 开发",
                          "weights": {"skill": 0.5, "jobtitle": 0.3, "exp": 0.2}},
                    headers=AUTH)
    assert r.status_code == 200
    assert r.json()["model"] == "rule"


def test_b01_invalid_weights_extra_field(client):
    # additionalProperties:false → 多余字段被拒（400 INVALID_PARAM）
    r = client.post("/internal/v1/ai/match",
                    json={"jd": "java", "resume": "java", "weights": {"skill": 0.5, "bogus": 1}},
                    headers=AUTH)
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_PARAM"


def test_b01_primary_deepseek(primary):
    c, orch = primary
    r = c.post("/internal/v1/ai/match",
               json={"jd": "java", "resume": "java"}, headers=AUTH)
    assert r.status_code == 200
    b = r.json()
    assert b["model"] == "deepseek"     # 注入 FakeLLM → 主链路
    assert b["score"] == 0.88
    assert b["matchedSkills"] == ["python", "fastapi"]
