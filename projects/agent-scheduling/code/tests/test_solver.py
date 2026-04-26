"""Tests for the batch solver (slice 11+)."""
from datetime import datetime

import pytest

from agent_scheduling.adapters.base import Event, TimeWindow
from agent_scheduling.solver import CandidateSlot, MeetingRequest, solve


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 5, 1, hour, minute)


_WINDOW = TimeWindow(start=_dt(8), end=_dt(18))


def _meeting(participants: tuple[str, ...] = ("u1", "u2"), duration: int = 60) -> MeetingRequest:
    return MeetingRequest(
        name="standup",
        participants=participants,
        duration_minutes=duration,
    )


# Slice 11: solver — single meeting


def test_solver_returns_first_available_slot_when_everyone_is_free():
    [slot] = solve([_meeting()], free_busy={"u1": [], "u2": []}, window=_WINDOW)
    assert slot.start == _dt(8)
    assert slot.end == _dt(9)
    assert slot.meeting_name == "standup"


def test_solver_avoids_busy_times():
    busy_morning = Event(title="busy", start=_dt(8), end=_dt(10))
    [slot] = solve(
        [_meeting()],
        free_busy={"u1": [busy_morning], "u2": []},
        window=_WINDOW,
    )
    assert slot.start == _dt(10)


def test_solver_returns_none_when_no_slot_fits():
    all_day = Event(title="busy", start=_dt(8), end=_dt(18))
    result = solve(
        [_meeting()],
        free_busy={"u1": [all_day], "u2": []},
        window=_WINDOW,
    )
    assert result is None


def test_solver_respects_meeting_duration():
    [slot] = solve(
        [_meeting(duration=120)],
        free_busy={"u1": [], "u2": []},
        window=_WINDOW,
    )
    assert (slot.end - slot.start).total_seconds() == 120 * 60


def test_solver_handles_empty_meeting_list():
    assert solve([], free_busy={}, window=_WINDOW) == []


def test_solver_treats_missing_participant_as_free():
    """If a participant has no entry in free_busy, treat them as fully available."""
    [slot] = solve([_meeting()], free_busy={"u1": []}, window=_WINDOW)
    assert slot.start == _dt(8)


def test_solver_steps_at_granularity():
    blocker = Event(title="busy", start=_dt(8), end=_dt(8, 15))
    [slot] = solve(
        [_meeting()],
        free_busy={"u1": [blocker], "u2": []},
        window=_WINDOW,
        granularity_minutes=30,
    )
    assert slot.start == _dt(8, 30)


def test_solver_carries_participants_into_slot():
    [slot] = solve([_meeting(participants=("u1", "u2", "u3"))],
                   free_busy={}, window=_WINDOW)
    assert slot.participants == ("u1", "u2", "u3")


# Slice 13: multi-meeting batch with shared participants


def test_two_meetings_same_participants_get_different_slots():
    m1 = MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60)
    m2 = MeetingRequest(name="m2", participants=("u1", "u2"), duration_minutes=60)
    result = solve([m1, m2], free_busy={"u1": [], "u2": []}, window=_WINDOW)
    assert result is not None
    [slot1, slot2] = result
    assert slot1.start != slot2.start
    assert not (slot1.end > slot2.start and slot1.start < slot2.end)


def test_three_meetings_with_overlapping_participants():
    """Cohort-style: triads sharing members must not collide for shared members."""
    triad_abc = MeetingRequest(
        name="abc", participants=("u1", "u2", "u3"), duration_minutes=60
    )
    triad_ade = MeetingRequest(
        name="ade", participants=("u1", "u4", "u5"), duration_minutes=60
    )
    triad_bdf = MeetingRequest(
        name="bdf", participants=("u2", "u4", "u6"), duration_minutes=60
    )
    result = solve(
        [triad_abc, triad_ade, triad_bdf],
        free_busy={f"u{i}": [] for i in range(1, 7)},
        window=_WINDOW,
    )
    assert result is not None
    by_name = {slot.meeting_name: slot for slot in result}

    def overlap_with_shared_members(a, b):
        shared = set(a.participants) & set(b.participants)
        if not shared:
            return False
        return a.end > b.start and a.start < b.end

    assert not overlap_with_shared_members(by_name["abc"], by_name["ade"])  # u1
    assert not overlap_with_shared_members(by_name["abc"], by_name["bdf"])  # u2
    assert not overlap_with_shared_members(by_name["ade"], by_name["bdf"])  # u4


def test_disjoint_participants_can_share_slot():
    """Meetings with no shared members may run concurrently."""
    m1 = MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60)
    m2 = MeetingRequest(name="m2", participants=("u3", "u4"), duration_minutes=60)
    result = solve([m1, m2], free_busy={}, window=_WINDOW)
    assert result is not None
    # The greedy solver picks the earliest slot for both; they may share start time.
    [slot1, slot2] = result
    assert slot1.start == _dt(8)
    assert slot2.start == _dt(8)


def test_infeasible_returns_none():
    """Two meetings, same participants, only one usable slot in window."""
    blocker = Event(title="busy", start=_dt(9), end=_dt(18))
    m1 = MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60)
    m2 = MeetingRequest(name="m2", participants=("u1", "u2"), duration_minutes=60)
    result = solve(
        [m1, m2],
        free_busy={"u1": [blocker], "u2": [blocker]},
        window=_WINDOW,
    )
    assert result is None


def test_solver_assigns_one_slot_per_meeting():
    meetings = [
        MeetingRequest(name=f"m{i}", participants=("u1", "u2"), duration_minutes=60)
        for i in range(4)
    ]
    result = solve(meetings, free_busy={}, window=_WINDOW)
    assert result is not None
    assert len(result) == 4
    assert {s.meeting_name for s in result} == {"m0", "m1", "m2", "m3"}


# Oracle: independent brute-force comparison


def _brute_force_feasible(meetings, free_busy, window):
    """Independent reference: try every combination of candidates."""
    from itertools import product
    from agent_scheduling.solver import _generate_candidates, _has_internal_conflict

    cands = [_generate_candidates(m, free_busy, window, 30) for m in meetings]
    if any(not c for c in cands):
        return False
    for combo in product(*cands):
        if not _has_internal_conflict(list(combo)):
            return True
    return False


def test_solver_matches_brute_force_oracle_on_tricky_instance():
    """Solver and brute force must agree on feasibility."""
    from agent_scheduling.solver import _generate_candidates, _has_internal_conflict
    busy_morning = Event(title="busy", start=_dt(8), end=_dt(12))
    meetings = [
        MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60),
        MeetingRequest(name="m2", participants=("u1", "u3"), duration_minutes=60),
        MeetingRequest(name="m3", participants=("u2", "u3"), duration_minutes=60),
    ]
    free_busy = {"u1": [busy_morning], "u2": [], "u3": []}
    solver_feasible = solve(meetings, free_busy, _WINDOW) is not None
    oracle_feasible = _brute_force_feasible(meetings, free_busy, _WINDOW)
    assert solver_feasible == oracle_feasible


# Slice 14: source-adapter assignment


def _slot(name: str = "m1") -> "CandidateSlot":
    from agent_scheduling.solver import CandidateSlot as _C
    return _C(
        meeting_name=name,
        start=_dt(9),
        end=_dt(10),
        participants=("u1", "u2"),
    )


def test_assign_sources_uses_per_meeting_override():
    from agent_scheduling.solver import assign_sources
    proposed = assign_sources(
        [_slot("triad-a"), _slot("triad-b")],
        source_map={
            "triad-a": ("user-alice", "adapter-alice-gmail"),
            "triad-b": ("user-bob", "adapter-bob-outlook"),
        },
    )
    assert proposed[0].source_user_id == "user-alice"
    assert proposed[0].source_adapter_id == "adapter-alice-gmail"
    assert proposed[1].source_user_id == "user-bob"
    assert proposed[1].source_adapter_id == "adapter-bob-outlook"


def test_assign_sources_falls_back_to_default():
    from agent_scheduling.solver import assign_sources
    proposed = assign_sources(
        [_slot("cohort-monthly")],
        source_map={},
        default=("user-leader", "adapter-leader-gmail"),
    )
    assert proposed[0].source_user_id == "user-leader"
    assert proposed[0].source_adapter_id == "adapter-leader-gmail"


def test_assign_sources_per_meeting_overrides_default():
    from agent_scheduling.solver import assign_sources
    proposed = assign_sources(
        [_slot("cohort-monthly"), _slot("triad-a")],
        source_map={"triad-a": ("user-alice", "adapter-alice")},
        default=("user-leader", "adapter-leader"),
    )
    by_name = {p.meeting_name: p for p in proposed}
    assert by_name["cohort-monthly"].source_user_id == "user-leader"
    assert by_name["triad-a"].source_user_id == "user-alice"


def test_assign_sources_raises_when_no_assignment_or_default():
    from agent_scheduling.solver import assign_sources
    with pytest.raises(ValueError):
        assign_sources([_slot("orphan")], source_map={}, default=None)


def test_proposed_meeting_preserves_slot_data():
    from agent_scheduling.solver import assign_sources
    [proposed] = assign_sources(
        [_slot("m1")],
        source_map={"m1": ("user-leader", "adapter-1")},
    )
    assert proposed.meeting_name == "m1"
    assert proposed.start == _dt(9)
    assert proposed.end == _dt(10)
    assert proposed.participants == ("u1", "u2")


# Slice 17: deadlock analysis


def test_analyze_deadlock_identifies_user_with_full_calendar():
    """If u1 is busy all day, u1 is clearly the binder."""
    from agent_scheduling.solver import analyze_deadlock
    all_day = Event(title="busy", start=_dt(8), end=_dt(18))
    meeting = MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60)
    binders = analyze_deadlock(
        [meeting], free_busy={"u1": [all_day], "u2": []}, window=_WINDOW
    )
    assert binders[0] == "u1"


def test_analyze_deadlock_returns_empty_when_everyone_is_free():
    """No deadlock at all, but the function should still be safe to call."""
    from agent_scheduling.solver import analyze_deadlock
    meeting = MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60)
    binders = analyze_deadlock(
        [meeting], free_busy={"u1": [], "u2": []}, window=_WINDOW
    )
    assert binders == []


# Slice 18: relaxations


def test_apply_relaxations_drops_named_meeting():
    from agent_scheduling.solver import apply_relaxations
    m1 = MeetingRequest(name="m1", participants=("u1",), duration_minutes=60)
    m2 = MeetingRequest(name="m2", participants=("u1",), duration_minutes=60)
    relaxed = apply_relaxations(
        [m1, m2],
        [{"kind": "drop_meeting", "details": {"meeting_name": "m1"}}],
    )
    assert relaxed == [m2]


def test_apply_relaxations_no_op_when_meeting_not_found():
    from agent_scheduling.solver import apply_relaxations
    m1 = MeetingRequest(name="m1", participants=("u1",), duration_minutes=60)
    relaxed = apply_relaxations(
        [m1], [{"kind": "drop_meeting", "details": {"meeting_name": "ghost"}}]
    )
    assert relaxed == [m1]


def test_apply_relaxations_unknown_kind_is_passthrough():
    from agent_scheduling.solver import apply_relaxations
    m1 = MeetingRequest(name="m1", participants=("u1",), duration_minutes=60)
    relaxed = apply_relaxations(
        [m1], [{"kind": "future_kind_we_do_not_know_yet", "details": {}}]
    )
    assert relaxed == [m1]


def test_resolve_after_drop_meeting_succeeds_when_originally_infeasible():
    """End-to-end: deadlock -> drop a meeting -> re-solve succeeds."""
    from agent_scheduling.solver import apply_relaxations
    blocker = Event(title="busy", start=_dt(8), end=_dt(18))
    m1 = MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60)
    m2 = MeetingRequest(name="m2", participants=("u1", "u2"), duration_minutes=60)

    free_busy = {"u1": [], "u2": [blocker]}  # u2 blocked all day
    assert solve([m1, m2], free_busy, _WINDOW) is None

    # User u2 says: drop m2.
    relaxed = apply_relaxations(
        [m1, m2], [{"kind": "drop_meeting", "details": {"meeting_name": "m2"}}]
    )
    # Now m1 is the only meeting, but u2 is still fully blocked. Still infeasible.
    assert solve(relaxed, free_busy, _WINDOW) is None

    # Try a different relaxation: free up u2.
    free_busy_relaxed = {"u1": [], "u2": []}
    assert solve(relaxed, free_busy_relaxed, _WINDOW) is not None


def test_analyze_deadlock_ranks_by_blocking_count():
    """When deadlocked, the user who blocks more slots ranks higher."""
    from agent_scheduling.solver import analyze_deadlock
    # u2 fully blocked → no slot is viable for the meeting (deadlock).
    # u1 has only one minor block; u2 blocks every slot.
    minor = Event(title="minor", start=_dt(8), end=_dt(9))
    all_day = Event(title="major", start=_dt(8), end=_dt(18))
    meeting = MeetingRequest(name="m1", participants=("u1", "u2"), duration_minutes=60)
    binders = analyze_deadlock(
        [meeting],
        free_busy={"u1": [minor], "u2": [all_day]},
        window=_WINDOW,
    )
    assert binders[0] == "u2"
