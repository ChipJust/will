"""Constraint-satisfaction solver for batch scheduling.

Single-meeting scheduling (slice 11), multi-meeting batches with overlapping
participants (slice 13), source-adapter assignment (slice 14), deadlock
analysis (slice 17). Algorithm: candidate generation per meeting + backtracking
with shared-participant conflict checking. Tractable for cohort-scale batches.
"""
from __future__ import annotations

import itertools
from collections import defaultdict
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


@dataclass(frozen=True)
class ProposedMeeting:
    """A solver slot bound to a source account responsible for sending the invite."""
    meeting_name: str
    start: datetime
    end: datetime
    participants: tuple[str, ...]
    source_user_id: str
    source_adapter_id: str


def assign_sources(
    slots: list[CandidateSlot],
    source_map: dict[str, tuple[str, str]],
    default: tuple[str, str] | None = None,
) -> list[ProposedMeeting]:
    """Bind each slot to a (source_user_id, source_adapter_id) tuple.

    `source_map` provides per-meeting overrides (keyed by meeting name).
    `default` is the fallback (typically the group leader). If neither
    is present for a slot, raises ValueError.
    """
    proposed: list[ProposedMeeting] = []
    for slot in slots:
        if slot.meeting_name in source_map:
            source_user_id, source_adapter_id = source_map[slot.meeting_name]
        elif default is not None:
            source_user_id, source_adapter_id = default
        else:
            raise ValueError(
                f"No source assignment for meeting '{slot.meeting_name}' and no default."
            )
        proposed.append(
            ProposedMeeting(
                meeting_name=slot.meeting_name,
                start=slot.start,
                end=slot.end,
                participants=slot.participants,
                source_user_id=source_user_id,
                source_adapter_id=source_adapter_id,
            )
        )
    return proposed


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


def analyze_deadlock(
    meetings: list[MeetingRequest],
    free_busy: dict[str, list[Event]],
    window: TimeWindow,
    granularity_minutes: int = 30,
) -> list[str]:
    """Identify the most-binding users when scheduling is infeasible.

    Returns [] if scheduling is actually feasible. Otherwise, ranks users by
    how many candidate slots their busy events block, summed across the meetings
    they participate in. For backtracking-exhaustion cases where every meeting
    has candidates but no combination fits, falls back to ranking by participation
    in the most-constrained meetings.
    """
    if solve(meetings, free_busy, window, granularity_minutes) is not None:
        return []

    block_score: dict[str, int] = defaultdict(int)

    for meeting in meetings:
        # Count slots each participant blocks for this specific meeting.
        duration = timedelta(minutes=meeting.duration_minutes)
        step = timedelta(minutes=granularity_minutes)
        current = window.start
        slot_count = 0
        viable = 0
        while current + duration <= window.end:
            slot_end = current + duration
            slot_count += 1
            blockers_here = [
                p
                for p in meeting.participants
                if _conflicts(current, slot_end, free_busy.get(p, []))
            ]
            if not blockers_here:
                viable += 1
            else:
                for p in blockers_here:
                    block_score[p] += 1
            current += step
        # If the meeting is impossible (zero viable slots), bump every participant
        # so they all surface as binders even when no one was strictly worse.
        if slot_count > 0 and viable == 0:
            for p in meeting.participants:
                block_score[p] += 1

    if not block_score:
        # Backtracking exhaustion fallback: highlight users in the most meetings.
        meeting_counts: dict[str, int] = defaultdict(int)
        for meeting in meetings:
            for p in meeting.participants:
                meeting_counts[p] += 1
        ranked = sorted(meeting_counts.items(), key=lambda kv: -kv[1])
        return [u for u, c in ranked if c > 0]

    ranked = sorted(block_score.items(), key=lambda kv: -kv[1])
    return [u for u, c in ranked if c > 0]
