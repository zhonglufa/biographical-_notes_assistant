"""test_health.py — 存活探针（开放，k8s liveness）"""
def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "ok"
    assert "contractVersion" in b
