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
    """Stub: future slices add handlers for the remaining message types."""
    from agent_scheduling.protocol import Envelope
    alice = _alice()
    confirm = Envelope(
        room_id="r",
        negotiation_id="n",
        sender_agent_id="agent-bob",
        sender_user_id="user-bob",
        sequence_no=0,
        timestamp=_FIXED_TIME,
        message_type=MessageType.CONFIRM,
        body={},
    )
    alice.receive(confirm)  # CONFIRM handled in slice 16; for now should not crash
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


# Slice 15: PROPOSE + ACCEPT / COUNTER / DECLINE


def _proposed(name: str = "m1") -> "ProposedMeeting":
    from agent_scheduling.solver import ProposedMeeting as _PM
    return _PM(
        meeting_name=name,
        start=datetime(2026, 5, 1, 9, 0),
        end=datetime(2026, 5, 1, 10, 0),
        participants=("u1", "u2"),
        source_user_id="user-alice",
        source_adapter_id="adapter-alice-gmail",
    )


def test_propose_emits_envelope_of_correct_type():
    env = _alice().propose("r", "n", "prop-1", [_proposed()])
    assert env.message_type == MessageType.PROPOSE


def test_propose_records_proposal_internally():
    alice = _alice()
    alice.propose("r", "n", "prop-1", [_proposed("m1"), _proposed("m2")])
    assert "prop-1" in alice.proposals_emitted
    assert len(alice.proposals_emitted["prop-1"]) == 2


def test_propose_round_trips_through_json():
    from agent_scheduling.protocol import Envelope as Env
    env = _alice().propose("r", "n", "prop-1", [_proposed()])
    decoded = Env.from_json(env.to_json())
    assert decoded == env


def test_accept_emits_envelope_with_proposal_id():
    env = _alice().accept("r", "n", "prop-1")
    assert env.message_type == MessageType.ACCEPT
    assert env.body["proposal_id"] == "prop-1"


def test_decline_carries_reason():
    env = _alice().decline("r", "n", "prop-1", reason="conflicts with travel")
    assert env.message_type == MessageType.DECLINE
    assert env.body["reason"] == "conflicts with travel"


def test_counter_carries_alternative_meetings():
    alt = [_proposed("alt-1")]
    env = _alice().counter("r", "n", "prop-1", alternative=alt)
    assert env.message_type == MessageType.COUNTER
    assert len(env.body["alternative"]) == 1
    assert env.body["alternative"][0]["meeting_name"] == "alt-1"


def test_receive_propose_records_proposal():
    alice = _alice()
    bob_propose = _bob().propose("r", "n", "prop-2", [_proposed("m1")])
    alice.receive(bob_propose)
    assert alice.proposals_received["prop-2"][0].meeting_name == "m1"


def test_receive_responses_tracked_per_agent():
    alice = _alice()
    alice.receive(_bob().accept("r", "n", "prop-1"))
    assert alice.proposal_responses["prop-1"]["agent-bob"] == "ACCEPT"


def test_unanimous_accept_when_all_responders_accept():
    alice = _alice()
    alice.receive(_bob().accept("r", "n", "prop-1"))
    # Only bob is expected; alice is the proposer.
    assert alice.has_unanimous_accept("prop-1", expected_responders={"agent-bob"})


def test_not_unanimous_when_one_declines():
    alice = _alice()
    alice.receive(_bob().decline("r", "n", "prop-1"))
    assert not alice.has_unanimous_accept("prop-1", expected_responders={"agent-bob"})


def test_not_unanimous_when_responder_missing():
    alice = _alice()
    alice.receive(_bob().accept("r", "n", "prop-1"))
    assert not alice.has_unanimous_accept(
        "prop-1", expected_responders={"agent-bob", "agent-carol"}
    )


def test_end_to_end_two_agents_reach_unanimous_accept():
    alice = _alice()
    bob = _bob()

    alice.receive(bob.hello("r", "n"))
    bob.receive(alice.hello("r", "n"))
    assert alice.peers and bob.peers

    alice_propose = alice.propose("r", "n", "prop-cohort", [_proposed("cohort")])
    bob.receive(alice_propose)
    assert "prop-cohort" in bob.proposals_received

    alice.receive(bob.accept("r", "n", "prop-cohort"))
    assert alice.has_unanimous_accept(
        "prop-cohort", expected_responders={"agent-bob"}
    )


# Slice 16: CONFIRM triggers send_invite for owned meetings


def _alice_with_adapter():
    from agent_scheduling.adapters import MockAdapter
    adapter = MockAdapter(send_address="alice@example.com")
    alice = Negotiator(
        agent_id="agent-alice",
        user_id="user-alice",
        capabilities=["BATCH_SCHEDULE"],
        clock=lambda: _FIXED_TIME,
        adapters={"adapter-alice-gmail": adapter},
    )
    return alice, adapter


def _bob_with_adapter():
    from agent_scheduling.adapters import MockAdapter
    adapter = MockAdapter(send_address="bob@example.com")
    bob = Negotiator(
        agent_id="agent-bob",
        user_id="user-bob",
        capabilities=["BATCH_SCHEDULE"],
        clock=lambda: _FIXED_TIME,
        adapters={"adapter-bob-gmail": adapter},
    )
    return bob, adapter


def test_confirm_emits_envelope_with_proposal_id():
    alice, _ = _alice_with_adapter()
    env = alice.confirm("r", "n", "prop-1")
    assert env.message_type == MessageType.CONFIRM
    assert env.body["proposal_id"] == "prop-1"


def test_confirm_triggers_send_invite_for_owned_meeting():
    alice, alice_adapter = _alice_with_adapter()
    alice.propose("r", "n", "prop-1", [_proposed("cohort")])  # alice owns this
    alice.confirm("r", "n", "prop-1")
    assert len(alice_adapter.sent_invites) == 1
    assert alice_adapter.sent_invites[0].title == "cohort"


def test_confirm_does_not_send_for_meetings_owned_by_other_users():
    alice, alice_adapter = _alice_with_adapter()
    bob_owned = ProposedMeeting(
        meeting_name="bob-meeting",
        start=datetime(2026, 5, 1, 9, 0),
        end=datetime(2026, 5, 1, 10, 0),
        participants=("u1", "u2"),
        source_user_id="user-bob",
        source_adapter_id="adapter-bob-gmail",
    )
    alice.propose("r", "n", "prop-1", [bob_owned])
    alice.confirm("r", "n", "prop-1")
    assert alice_adapter.sent_invites == []


def test_confirm_is_idempotent():
    alice, alice_adapter = _alice_with_adapter()
    alice.propose("r", "n", "prop-1", [_proposed("cohort")])
    alice.confirm("r", "n", "prop-1")
    alice.confirm("r", "n", "prop-1")  # second confirm should not double-send
    assert len(alice_adapter.sent_invites) == 1


def test_receive_confirm_triggers_send_invite():
    alice, alice_adapter = _alice_with_adapter()
    bob, _ = _bob_with_adapter()
    # alice is the proposal source (alice owns the meeting); bob receives the proposal
    alice_propose = alice.propose("r", "n", "prop-1", [_proposed("cohort")])
    bob.receive(alice_propose)
    # bob emits CONFIRM; alice receives it and sends invite for her owned meeting
    bob_confirm = bob.confirm("r", "n", "prop-1")
    alice.receive(bob_confirm)
    assert len(alice_adapter.sent_invites) == 1


def test_invite_results_recorded_per_proposal():
    alice, _ = _alice_with_adapter()
    alice.propose("r", "n", "prop-1", [_proposed("m1"), _proposed("m2")])
    alice.confirm("r", "n", "prop-1")
    assert len(alice.sent_invite_results["prop-1"]) == 2
    assert all(r.success for r in alice.sent_invite_results["prop-1"])


# Required for ProposedMeeting reference in tests above
from agent_scheduling.solver import ProposedMeeting


# Slice 17: DEADLOCK_ASK emission


def test_deadlock_ask_emits_envelope():
    env = _alice().deadlock_ask(
        room_id="r",
        negotiation_id="n",
        proposal_id="prop-1",
        binding_users=["user-bob", "user-carol"],
        suggestion="could you skip meeting m3 next month?",
    )
    assert env.message_type == MessageType.DEADLOCK_ASK
    assert env.body["binding_users"] == ["user-bob", "user-carol"]
    assert env.body["suggestion"] == "could you skip meeting m3 next month?"


def test_deadlock_ask_round_trips_through_json():
    from agent_scheduling.protocol import Envelope as Env
    env = _alice().deadlock_ask(
        "r", "n", "prop-1", binding_users=["user-bob"], suggestion="?"
    )
    assert Env.from_json(env.to_json()) == env


# Slice 18: DEADLOCK_RELAX message


def test_deadlock_relax_emits_envelope_of_correct_type():
    env = _alice().deadlock_relax(
        room_id="r",
        negotiation_id="n",
        proposal_id="prop-1",
        relaxation_kind="drop_meeting",
        details={"meeting_name": "m2"},
    )
    assert env.message_type == MessageType.DEADLOCK_RELAX
    assert env.body["relaxation_kind"] == "drop_meeting"
    assert env.body["details"]["meeting_name"] == "m2"


def test_receive_deadlock_relax_records_relaxation():
    alice = _alice()
    bob_relax = _bob().deadlock_relax(
        "r", "n", "prop-1", "drop_meeting", {"meeting_name": "m2"}
    )
    alice.receive(bob_relax)
    relaxations = alice.relaxations_received["prop-1"]
    assert len(relaxations) == 1
    assert relaxations[0]["kind"] == "drop_meeting"
    assert relaxations[0]["user_id"] == "user-bob"


def test_deadlock_relax_round_trips_through_json():
    from agent_scheduling.protocol import Envelope as Env
    env = _alice().deadlock_relax(
        "r", "n", "prop-1", "drop_meeting", {"meeting_name": "m2"}
    )
    assert Env.from_json(env.to_json()) == env


# Slice 19: state persistence (crash recovery)


def _populated_alice():
    """Alice with non-trivial state: peers, free/busy, proposal, response, relaxation."""
    alice, _ = _alice_with_adapter()
    bob, _ = _bob_with_adapter()
    alice.receive(bob.hello("r", "n"))
    alice.peer_free_busy["agent-bob"] = [
        _busy_event(),
    ]
    alice.propose("r", "n", "prop-1", [_proposed("cohort")])
    alice.receive(bob.accept("r", "n", "prop-1"))
    alice.receive(
        bob.deadlock_relax("r", "n", "prop-2", "drop_meeting", {"meeting_name": "m2"})
    )
    return alice


def test_save_state_writes_a_json_file(tmp_path):
    alice, _ = _alice_with_adapter()
    path = tmp_path / "state.json"
    alice.save_state(path)
    assert path.exists()
    import json
    parsed = json.loads(path.read_text())
    assert parsed["agent_id"] == "agent-alice"


def test_load_state_round_trips_full_state(tmp_path):
    original = _populated_alice()
    path = tmp_path / "state.json"
    original.save_state(path)

    restored, _ = _alice_with_adapter()
    restored.load_state(path)

    assert restored.peers == original.peers
    assert restored.peer_free_busy == original.peer_free_busy
    assert restored.proposals_emitted == original.proposals_emitted
    assert restored.proposal_responses == original.proposal_responses
    assert restored.relaxations_received == original.relaxations_received
    assert restored._sequence_no == original._sequence_no


def test_load_state_preserves_sequence_continuity(tmp_path):
    """After restore, next emit should pick up where the old one left off."""
    alice, _ = _alice_with_adapter()
    alice.hello("r", "n")  # seq 0
    alice.hello("r", "n")  # seq 1
    path = tmp_path / "state.json"
    alice.save_state(path)

    restored, _ = _alice_with_adapter()
    restored.load_state(path)
    next_env = restored.hello("r", "n")
    assert next_env.sequence_no == 2


def test_load_state_refuses_mismatched_agent_id(tmp_path):
    alice, _ = _alice_with_adapter()
    path = tmp_path / "state.json"
    alice.save_state(path)

    bob, _ = _bob_with_adapter()
    import pytest
    with pytest.raises(ValueError):
        bob.load_state(path)


def test_load_state_into_fresh_negotiator_does_not_send_duplicate_invites(tmp_path):
    """Crash-recovery scenario: invites already sent before restart should not re-fire."""
    alice, alice_adapter = _alice_with_adapter()
    alice.propose("r", "n", "prop-1", [_proposed("cohort")])
    alice.confirm("r", "n", "prop-1")
    assert len(alice_adapter.sent_invites) == 1

    path = tmp_path / "state.json"
    alice.save_state(path)

    restored, restored_adapter = _alice_with_adapter()
    restored.load_state(path)
    # Replay confirm — should not double-send (idempotency preserved across restart)
    restored.confirm("r", "n", "prop-1")
    assert len(restored_adapter.sent_invites) == 0  # already sent in prior session
