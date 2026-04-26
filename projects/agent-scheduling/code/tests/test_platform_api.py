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
        ws_b.send_json({"kind": "user", "text": "another in B"})
        echo2 = ws_b.receive_json()
        assert echo2["text"] == "another in B"


# Slice 22: kind field validation


def test_ws_user_kind_round_trips():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-22a") as ws:
        ws.send_json({"kind": "user", "text": "hello from a human"})
        echo = ws.receive_json()
        assert echo["kind"] == "user"
        assert echo["text"] == "hello from a human"


def test_ws_agent_kind_round_trips():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-22b") as ws:
        ws.send_json(
            {"kind": "agent", "protocol_message_type": "HELLO", "body": {}}
        )
        echo = ws.receive_json()
        assert echo["kind"] == "agent"
        assert echo["protocol_message_type"] == "HELLO"


def test_ws_invalid_kind_returns_error_and_does_not_persist():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-22c") as ws:
        ws.send_json({"kind": "robot", "text": "from a robot"})
        resp = ws.receive_json()
        assert resp["error"] == "invalid_kind"
    # New subscriber should see no history (the bad message was rejected).
    with client.websocket_connect("/ws/room-22c") as ws2:
        ws2.send_json({"kind": "user", "text": "post-rejection"})
        echo = ws2.receive_json()
        # If the bad message had been persisted, it would replay first. Since
        # we got our echo right away, the bad message is gone.
        assert echo["text"] == "post-rejection"


def test_ws_missing_kind_returns_error():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-22d") as ws:
        ws.send_json({"text": "no kind set"})
        resp = ws.receive_json()
        assert resp["error"] == "invalid_kind"


# Slice 23: broadcast to all clients in a room


def test_message_from_one_client_reaches_other_client_in_same_room():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-23a") as ws_a:
        with client.websocket_connect("/ws/room-23a") as ws_b:
            ws_a.send_json({"kind": "user", "text": "hello room"})
            assert ws_a.receive_json()["text"] == "hello room"
            assert ws_b.receive_json()["text"] == "hello room"


def test_agent_protocol_message_round_trips_with_protocol_message_type():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-23b") as ws_a:
        with client.websocket_connect("/ws/room-23b") as ws_b:
            ws_a.send_json(
                {
                    "kind": "agent",
                    "protocol_message_type": "BATCH_SCHEDULE",
                    "body": {"meetings": []},
                }
            )
            received = ws_b.receive_json()
            assert received["kind"] == "agent"
            assert received["protocol_message_type"] == "BATCH_SCHEDULE"
            assert received["body"] == {"meetings": []}
            ws_a.receive_json()  # consume sender's copy


def test_broadcast_does_not_cross_rooms():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/room-23c") as ws_a:
        with client.websocket_connect("/ws/room-23d") as ws_b:
            ws_a.send_json({"kind": "user", "text": "in c only"})
            ws_a.receive_json()
            # ws_b should not receive — exercise this by sending its own
            # message and confirming the next receive is its own echo, not
            # ws_a's message.
            ws_b.send_json({"kind": "user", "text": "in d only"})
            received = ws_b.receive_json()
            assert received["text"] == "in d only"
