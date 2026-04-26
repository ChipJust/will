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
