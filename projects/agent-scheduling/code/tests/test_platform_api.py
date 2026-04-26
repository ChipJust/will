"""Tests for the platform API (slice 20+)."""
from fastapi.testclient import TestClient

from agent_scheduling.platform import create_app


# Slice 20: /health


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_health_endpoint_uses_correct_method():
    client = TestClient(create_app())
    assert client.post("/health").status_code == 405


def test_app_has_title():
    app = create_app()
    assert app.title == "agent-scheduling platform"
