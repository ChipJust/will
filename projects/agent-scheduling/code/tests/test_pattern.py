"""Tests for MeetingPattern (slice 8)."""
from agent_scheduling.pattern import MeetingPattern, RecurringMeetingSpec


def _cohort_pattern() -> MeetingPattern:
    cohort_meeting = RecurringMeetingSpec(
        name="cohort-monthly",
        participants=("u1", "u2", "u3", "u4", "u5", "u6", "u7"),
        duration_minutes=90,
        count_per_period=1,
        period="month",
    )
    triad_a = RecurringMeetingSpec(
        name="triad-a",
        participants=("u1", "u2", "u3"),
        duration_minutes=60,
        count_per_period=3,
        period="month",
    )
    return MeetingPattern(
        group_id="cohort-2026",
        recurring_meetings=[cohort_meeting, triad_a],
    )


def test_meeting_pattern_can_be_constructed():
    pattern = _cohort_pattern()
    assert pattern.group_id == "cohort-2026"
    assert len(pattern.recurring_meetings) == 2


def test_meeting_pattern_round_trips_through_json():
    original = _cohort_pattern()
    encoded = original.to_json()
    decoded = MeetingPattern.from_json(encoded)
    assert decoded == original


def test_recurring_meeting_spec_defaults():
    spec = RecurringMeetingSpec(
        name="weekly-1on1",
        participants=("u1", "u2"),
        duration_minutes=30,
    )
    assert spec.count_per_period == 1
    assert spec.period == "month"


def test_meeting_pattern_with_no_recurring_meetings():
    empty = MeetingPattern(group_id="g1")
    assert empty.recurring_meetings == []
    assert MeetingPattern.from_json(empty.to_json()) == empty


def test_serialized_pattern_is_valid_json():
    import json as _json
    pattern = _cohort_pattern()
    parsed = _json.loads(pattern.to_json())
    assert parsed["group_id"] == "cohort-2026"
    assert isinstance(parsed["recurring_meetings"], list)
