"""Tests for the protocol envelope (slice 9)."""
import json
from datetime import datetime

import pytest

from agent_scheduling.protocol import Envelope, MessageType


def _envelope(message_type: MessageType = MessageType.HELLO, **overrides) -> Envelope:
    base = dict(
        room_id="room-1",
        negotiation_id="neg-42",
        sender_agent_id="agent-alice",
        sender_user_id="user-alice",
        sequence_no=0,
        timestamp=datetime(2026, 5, 1, 9, 0),
        message_type=message_type,
        body={"capabilities": ["BATCH_SCHEDULE"]},
    )
    base.update(overrides)
    return Envelope(**base)


def test_envelope_can_be_constructed():
    env = _envelope()
    assert env.message_type == MessageType.HELLO
    assert env.sequence_no == 0


def test_envelope_round_trips_through_json():
    original = _envelope()
    decoded = Envelope.from_json(original.to_json())
    assert decoded == original


def test_envelope_serializes_datetime_as_iso():
    env = _envelope(timestamp=datetime(2026, 5, 1, 9, 0))
    parsed = json.loads(env.to_json())
    assert parsed["timestamp"] == "2026-05-01T09:00:00"


def test_envelope_serializes_message_type_as_string():
    env = _envelope(message_type=MessageType.BATCH_SCHEDULE)
    parsed = json.loads(env.to_json())
    assert parsed["message_type"] == "BATCH_SCHEDULE"


def test_envelope_round_trip_preserves_complex_body():
    body = {"meetings": [{"name": "cohort", "duration_minutes": 90}], "n": 7}
    env = _envelope(body=body)
    decoded = Envelope.from_json(env.to_json())
    assert decoded.body == body


def test_envelope_default_body_is_empty_dict():
    env = Envelope(
        room_id="r",
        negotiation_id="n",
        sender_agent_id="a",
        sender_user_id="u",
        sequence_no=0,
        timestamp=datetime(2026, 5, 1, 9, 0),
        message_type=MessageType.HELLO,
    )
    assert env.body == {}


def test_message_type_covers_all_protocol_messages():
    """Spec lists 10 message types; the enum must cover all of them."""
    expected = {
        "HELLO",
        "BATCH_SCHEDULE",
        "FREE_BUSY",
        "PROPOSE",
        "ACCEPT",
        "COUNTER",
        "DECLINE",
        "CONFIRM",
        "DEADLOCK_ASK",
        "DEADLOCK_RELAX",
    }
    assert {m.value for m in MessageType} == expected


def test_unknown_message_type_string_raises():
    with pytest.raises(ValueError):
        MessageType("BOGUS")
