"""Constraint-satisfaction solver for batch scheduling.

Single-meeting scheduling (slice 11) and multi-meeting batches with overlapping
participants (slice 13). Algorithm: candidate generation per meeting + backtracking
with shared-participant conflict checking. Tractable for cohort-scale batches.
"""
from __future__ import annotations

import itertools
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


def _slots_overlap(a: CandidateSlot, b: CandidateSlot) -> bool:
    return a.end > b.start and a.start < b.end


def _share_participant(a: CandidateSlot, b: CandidateSlot) -> bool:
    return bool(set(a.participants) & set(b.participants))


def _generate_candidates(
    meeting: MeetingRequest,
    free_busy: dict[str, list[Event]],
    window: TimeWindow,
    granularity_minutes: int,
) -> list[CandidateSlot]:
    duration = timedelta(minutes=meeting.duration_minutes)
    step = timedelta(minutes=granularity_minutes)
    candidates: list[CandidateSlot] = []
    current = window.start
    while current + duration <= window.end:
        end = current + duration
        if all(
            not _conflicts(current, end, free_busy.get(participant, []))
            for participant in meeting.participants
        ):
            candidates.append(
                CandidateSlot(
                    meeting_name=meeting.name,
                    start=current,
                    end=end,
                    participants=meeting.participants,
                )
            )
        current += step
    return candidates


def _has_internal_conflict(assignment: list[CandidateSlot]) -> bool:
    for a, b in itertools.combinations(assignment, 2):
        if _share_participant(a, b) and _slots_overlap(a, b):
            return True
    return False


def _backtrack(
    candidates_per_meeting: list[list[CandidateSlot]],
    assignment: list[CandidateSlot],
    idx: int,
) -> bool:
    if idx == len(candidates_per_meeting):
        return True
    for candidate in candidates_per_meeting[idx]:
        if not any(
            _share_participant(candidate, prior) and _slots_overlap(candidate, prior)
            for prior in assignment
        ):
            assignment.append(candidate)
            if _backtrack(candidates_per_meeting, assignment, idx + 1):
                return True
            assignment.pop()
    return False


def solve(
    meetings: list[MeetingRequest],
    free_busy: dict[str, list[Event]],
    window: TimeWindow,
    granularity_minutes: int = 30,
) -> list[CandidateSlot] | None:
    """Return one CandidateSlot per requested meeting, or None if infeasible."""
    if not meetings:
        return []

    candidates_per_meeting: list[list[CandidateSlot]] = []
    for meeting in meetings:
        candidates = _generate_candidates(
            meeting, free_busy, window, granularity_minutes
        )
        if not candidates:
            return None
        candidates_per_meeting.append(candidates)

    assignment: list[CandidateSlot] = []
    if _backtrack(candidates_per_meeting, assignment, 0):
        return assignment
    return None
