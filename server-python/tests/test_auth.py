"""test_auth.py — X-Internal-Token 鉴权（HLD §4.5 / §939）"""
from fastapi.testclient import TestClient

from helpers import AUTH, TOKEN


def test_healthz_open_without_token(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_match_missing_token_401(client):
    r = client.post("/internal/v1/ai/match", json={"jd": "x", "resume": "y"})
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"


def test_match_wrong_token_401(client):
    r = client.post("/internal/v1/ai/match", json={"jd": "x", "resume": "y"},
                    headers={"X-Internal-Token": "bad"})
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"


def test_match_correct_token_200(client):
    r = client.post("/internal/v1/ai/match", json={"jd": "java 开发", "resume": "熟悉 java"},
                    headers=AUTH)
    assert r.status_code == 200
    assert r.json()["model"] == "rule"  # 无 LLM key → 降级链


def test_missing_token_config_denies_all(no_token_config):
    from app.main import app
    with TestClient(app) as c:
        r = c.post("/internal/v1/ai/match", json={"jd": "x", "resume": "y"},
                   headers={"X-Internal-Token": TOKEN})
        assert r.status_code == 401
