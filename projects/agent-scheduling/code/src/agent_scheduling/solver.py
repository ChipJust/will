"""Constraint-satisfaction solver for batch scheduling.

Finds a slot per meeting that respects every participant's free/busy. Single-
meeting case is handled here (slice 11). Multi-meeting batch with overlapping
participants is layered on in slice 13.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from agent_scheduling.adapters.base import Event, TimeWindow


@dataclass(frozen=True)
class MeetingRequest:
    name: str
    participants: tuple[str, ...]
    duration_minutes: int


@dataclass(frozen=True)
class CandidateSlot:
    meeting_name: str
    start: datetime
    end: datetime
    participants: tuple[str, ...]


def _conflicts(start: datetime, end: datetime, events: list[Event]) -> bool:
    return any(event.end > start and event.start < end for event in events)


def _find_slot_for_meeting(
    meeting: MeetingRequest,
    free_busy: dict[str, list[Event]],
    window: TimeWindow,
    granularity_minutes: int,
) -> CandidateSlot | None:
    duration = timedelta(minutes=meeting.duration_minutes)
    step = timedelta(minutes=granularity_minutes)
    current = window.start
    while current + duration <= window.end:
        end = current + duration
        if all(
            not _conflicts(current, end, free_busy.get(participant, []))
            for participant in meeting.participants
        ):
            return CandidateSlot(
                meeting_name=meeting.name,
                start=current,
                end=end,
                participants=meeting.participants,
            )
        current += step
    return None


def solve(
    meetings: list[MeetingRequest],
    free_busy: dict[str, list[Event]],
    window: TimeWindow,
    granularity_minutes: int = 30,
) -> list[CandidateSlot] | None:
    """Return one CandidateSlot per requested meeting, or None if infeasible.

    Slice 11: single-meeting only. Slice 13 expands to multi-meeting batch.
    """
    if not meetings:
        return []
    if len(meetings) > 1:
        raise NotImplementedError(
            "Multi-meeting batch scheduling lands at slice 13."
        )
    slot = _find_slot_for_meeting(
        meetings[0], free_busy, window, granularity_minutes
    )
    return [slot] if slot is not None else None
