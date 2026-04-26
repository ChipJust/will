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


# Slice 11: BATCH_SCHEDULE emission


def test_batch_schedule_emits_envelope_of_correct_type():
    from agent_scheduling.solver import MeetingRequest
    env = _alice().batch_schedule(
        room_id="r",
        negotiation_id="n",
        meetings=[
            MeetingRequest(
                name="standup", participants=("u1", "u2"), duration_minutes=60
            )
        ],
        window_start=_FIXED_TIME,
        window_end=datetime(2026, 5, 1, 18, 0),
    )
    assert env.message_type == MessageType.BATCH_SCHEDULE


def test_batch_schedule_carries_meetings_in_body():
    from agent_scheduling.solver import MeetingRequest
    meeting = MeetingRequest(
        name="standup", participants=("u1", "u2"), duration_minutes=60
    )
    env = _alice().batch_schedule(
        room_id="r",
        negotiation_id="n",
        meetings=[meeting],
        window_start=_FIXED_TIME,
        window_end=datetime(2026, 5, 1, 18, 0),
    )
    body = env.body
    assert body["meetings"] == [
        {"name": "standup", "participants": ["u1", "u2"], "duration_minutes": 60}
    ]
    assert body["window_start"] == _FIXED_TIME.isoformat()


def test_batch_schedule_round_trips_through_json():
    from agent_scheduling.solver import MeetingRequest
    from agent_scheduling.protocol import Envelope as Env
    meeting = MeetingRequest(
        name="standup", participants=("u1", "u2"), duration_minutes=60
    )
    env = _alice().batch_schedule(
        room_id="r",
        negotiation_id="n",
        meetings=[meeting],
        window_start=_FIXED_TIME,
        window_end=datetime(2026, 5, 1, 18, 0),
    )
    decoded = Env.from_json(env.to_json())
    assert decoded == env


# Slice 12: FREE_BUSY with privacy filter


def _busy_event() -> "Event":
    from agent_scheduling.adapters.base import Event as _Event
    return _Event(
        title="1:1 with manager",
        start=datetime(2026, 5, 1, 9, 0),
        end=datetime(2026, 5, 1, 10, 0),
        attendees=("alice@x.com", "manager@x.com"),
        location="Office",
    )


def _window():
    from agent_scheduling.adapters.base import TimeWindow as _TW
    return _TW(
        start=datetime(2026, 5, 1, 8, 0),
        end=datetime(2026, 5, 1, 18, 0),
    )


def test_free_busy_emits_envelope_of_correct_type():
    from agent_scheduling.privacy import PrivacyPolicyStore
    env = _alice().free_busy(
        room_id="r",
        negotiation_id="n",
        viewer_user_id="user-bob",
        events=[_busy_event()],
        policy_store=PrivacyPolicyStore(),
        window=_window(),
    )
    assert env.message_type == MessageType.FREE_BUSY


def test_free_busy_default_policy_strips_metadata():
    """Default level is decision_only — title/attendees/location not revealed."""
    from agent_scheduling.privacy import PrivacyPolicyStore
    env = _alice().free_busy(
        room_id="r",
        negotiation_id="n",
        viewer_user_id="user-bob",
        events=[_busy_event()],
        policy_store=PrivacyPolicyStore(),
        window=_window(),
    )
    [event] = env.body["events"]
    assert event["title"] == "busy"
    assert event["attendees"] == []
    assert event["location"] is None
    assert env.body["level"] == "decision_only"


def test_free_busy_full_details_passes_metadata_through():
    from agent_scheduling.privacy import PrivacyLevel, PrivacyPolicyStore
    store = PrivacyPolicyStore()
    store.set(subject="user-alice", viewer="user-bob", level=PrivacyLevel.FULL_DETAILS)
    env = _alice().free_busy(
        room_id="r",
        negotiation_id="n",
        viewer_user_id="user-bob",
        events=[_busy_event()],
        policy_store=store,
        window=_window(),
    )
    [event] = env.body["events"]
    assert event["title"] == "1:1 with manager"
    assert event["attendees"] == ["alice@x.com", "manager@x.com"]


def test_free_busy_is_directional_per_viewer():
    """Same emitter, different viewers, different filter levels applied."""
    from agent_scheduling.privacy import PrivacyLevel, PrivacyPolicyStore
    store = PrivacyPolicyStore()
    store.set(subject="user-alice", viewer="user-bob", level=PrivacyLevel.FULL_DETAILS)
    store.set(subject="user-alice", viewer="user-carol", level=PrivacyLevel.BUSY_ONLY)
    alice = _alice()
    to_bob = alice.free_busy("r", "n", "user-bob", [_busy_event()], store, _window())
    to_carol = alice.free_busy("r", "n", "user-carol", [_busy_event()], store, _window())
    assert to_bob.body["events"][0]["title"] == "1:1 with manager"
    assert to_carol.body["events"][0]["title"] == "busy"


def test_receive_free_busy_records_peer_availability():
    from agent_scheduling.privacy import PrivacyPolicyStore
    bob_to_alice = _bob().free_busy(
        room_id="r",
        negotiation_id="n",
        viewer_user_id="user-alice",
        events=[_busy_event()],
        policy_store=PrivacyPolicyStore(),
        window=_window(),
    )
    alice = _alice()
    alice.receive(bob_to_alice)
    assert "agent-bob" in alice.peer_free_busy
    assert len(alice.peer_free_busy["agent-bob"]) == 1


def test_receive_free_busy_ignores_messages_addressed_to_others():
    from agent_scheduling.privacy import PrivacyPolicyStore
    bob_to_carol = _bob().free_busy(
        room_id="r",
        negotiation_id="n",
        viewer_user_id="user-carol",
        events=[_busy_event()],
        policy_store=PrivacyPolicyStore(),
        window=_window(),
    )
    alice = _alice()
    alice.receive(bob_to_carol)
    assert alice.peer_free_busy == {}


def test_free_busy_round_trips_through_json():
    from agent_scheduling.privacy import PrivacyPolicyStore
    from agent_scheduling.protocol import Envelope as Env
    env = _alice().free_busy(
        room_id="r",
        negotiation_id="n",
        viewer_user_id="user-bob",
        events=[_busy_event()],
        policy_store=PrivacyPolicyStore(),
        window=_window(),
    )
    assert Env.from_json(env.to_json()) == env
