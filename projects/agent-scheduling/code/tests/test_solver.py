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


def test_solver_raises_for_multi_meeting_batch_at_this_slice():
    """Slice 13 implements multi-meeting batches; until then the solver is
    explicit about what it doesn't yet do."""
    with pytest.raises(NotImplementedError):
        solve([_meeting(), _meeting()], free_busy={}, window=_WINDOW)
