"""Smoke tests — cheap checks that the app boots and core routes respond.
These run in CI on every push so a broken import or route fails the build."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root_serves_html():
    resp = client.get("/")
    assert resp.status_code == 200


def test_analyze_rejects_bad_body():
    # Missing required fields -> 422 proves request validation is wired up.
    resp = client.post("/analyze", json={})
    assert resp.status_code == 422
