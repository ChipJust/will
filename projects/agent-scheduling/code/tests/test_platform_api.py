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


# Slice 21: WebSocket room-join + history replay


def test_ws_connect_to_empty_room_replays_nothing():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-1") as ws:
        # Send a sentinel; the server echoes it back. No prior history was replayed.
        ws.send_json({"kind": "user", "text": "hi"})
        echoed = ws.receive_json()
        assert echoed == {"kind": "user", "text": "hi"}


def test_ws_replays_history_to_new_subscriber():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-2") as ws_a:
        ws_a.send_json({"kind": "user", "text": "first"})
        ws_a.receive_json()  # consume echo
        ws_a.send_json({"kind": "user", "text": "second"})
        ws_a.receive_json()
    # New subscriber connects after disconnect — should see both prior messages.
    with client.websocket_connect("/ws/room-2") as ws_b:
        first = ws_b.receive_json()
        second = ws_b.receive_json()
        assert first["text"] == "first"
        assert second["text"] == "second"


def test_ws_rooms_are_isolated():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-A") as ws_a:
        ws_a.send_json({"kind": "user", "text": "in A"})
        ws_a.receive_json()
    with client.websocket_connect("/ws/room-B") as ws_b:
        ws_b.send_json({"kind": "user", "text": "in B"})
        echo = ws_b.receive_json()
        assert echo["text"] == "in B"
        # Sending a sentinel and receiving once should be the only echo — no
        # cross-room replay. We can't easily assert "no more messages" without
        # blocking; instead, send a second message and confirm the next receive
        # is its echo.
        ws_b.send_json({"kind": "user", "text": "another in B"})
        echo2 = ws_b.receive_json()
        assert echo2["text"] == "another in B"
