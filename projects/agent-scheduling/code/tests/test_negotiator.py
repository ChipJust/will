"""Tests for Negotiator (slices 10+)."""
from datetime import datetime

from agent_scheduling.negotiator import Negotiator
from agent_scheduling.protocol import MessageType


_FIXED_TIME = datetime(2026, 5, 1, 9, 0)


def _alice() -> Negotiator:
    return Negotiator(
        agent_id="agent-alice",
        user_id="user-alice",
        capabilities=["BATCH_SCHEDULE", "DEADLOCK_RELAX"],
        clock=lambda: _FIXED_TIME,
    )


def _bob() -> Negotiator:
    return Negotiator(
        agent_id="agent-bob",
        user_id="user-bob",
        capabilities=["BATCH_SCHEDULE"],
        clock=lambda: _FIXED_TIME,
    )


# Slice 10: HELLO


def test_hello_emits_envelope_of_correct_type():
    env = _alice().hello(room_id="room-1", negotiation_id="neg-1")
    assert env.message_type == MessageType.HELLO


def test_hello_carries_sender_identity():
    env = _alice().hello(room_id="room-1", negotiation_id="neg-1")
    assert env.sender_agent_id == "agent-alice"
    assert env.sender_user_id == "user-alice"


def test_hello_carries_capabilities_in_body():
    env = _alice().hello(room_id="room-1", negotiation_id="neg-1")
    assert env.body["capabilities"] == ["BATCH_SCHEDULE", "DEADLOCK_RELAX"]


def test_hello_uses_injected_clock():
    env = _alice().hello(room_id="room-1", negotiation_id="neg-1")
    assert env.timestamp == _FIXED_TIME


def test_sequence_no_increments_per_emit():
    alice = _alice()
    e1 = alice.hello(room_id="r", negotiation_id="n")
    e2 = alice.hello(room_id="r", negotiation_id="n")
    assert e1.sequence_no == 0
    assert e2.sequence_no == 1


def test_receive_hello_records_peer_capabilities():
    alice = _alice()
    bob_hello = _bob().hello(room_id="r", negotiation_id="n")
    alice.receive(bob_hello)
    assert alice.peers == {"agent-bob": ["BATCH_SCHEDULE"]}


def test_two_negotiators_can_exchange_hello():
    alice = _alice()
    bob = _bob()
    alice.receive(bob.hello(room_id="r", negotiation_id="n"))
    bob.receive(alice.hello(room_id="r", negotiation_id="n"))
    assert alice.peers == {"agent-bob": ["BATCH_SCHEDULE"]}
    assert bob.peers == {"agent-alice": ["BATCH_SCHEDULE", "DEADLOCK_RELAX"]}


def test_receive_ignores_messages_of_other_types_for_now():
    """Stub: future slices add handlers; HELLO-only is the slice 10 invariant."""
    from agent_scheduling.protocol import Envelope
    alice = _alice()
    propose = Envelope(
        room_id="r",
        negotiation_id="n",
        sender_agent_id="agent-bob",
        sender_user_id="user-bob",
        sequence_no=0,
        timestamp=_FIXED_TIME,
        message_type=MessageType.PROPOSE,
        body={},
    )
    alice.receive(propose)  # should not crash, no peer recorded for non-HELLO
    assert alice.peers == {}
