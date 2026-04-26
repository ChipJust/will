"""Tests for the directional privacy filter (slices 6 + 7)."""
from datetime import datetime

import pytest

from agent_scheduling.adapters.base import Event
from agent_scheduling.privacy import PrivacyLevel, apply_filter


def _dt(hour: int) -> datetime:
    return datetime(2026, 5, 1, hour, 0)


_EVENTS = [
    Event(
        title="standup",
        start=_dt(9),
        end=_dt(10),
        attendees=("alice@x.com", "bob@x.com"),
        location="Zoom",
    ),
    Event(
        title="1:1 with Alice",
        start=_dt(14),
        end=_dt(15),
        attendees=("alice@x.com",),
        location="Coffee shop",
    ),
]


# Slice 6: filter levels


def test_full_details_passes_through_events():
    result = apply_filter(_EVENTS, PrivacyLevel.FULL_DETAILS)
    assert result == _EVENTS


def test_busy_only_strips_metadata_keeping_times():
    result = apply_filter(_EVENTS, PrivacyLevel.BUSY_ONLY)
    assert len(result) == 2
    for original, filtered in zip(_EVENTS, result):
        assert filtered.title == "busy"
        assert filtered.attendees == ()
        assert filtered.location is None
        assert filtered.start == original.start
        assert filtered.end == original.end


def test_decision_only_strips_metadata_at_this_slice():
    """Without negotiation context, decision_only currently degrades to busy_only."""
    busy = apply_filter(_EVENTS, PrivacyLevel.BUSY_ONLY)
    decision = apply_filter(_EVENTS, PrivacyLevel.DECISION_ONLY)
    assert busy == decision


def test_full_details_returns_a_copy_not_the_original_list():
    result = apply_filter(_EVENTS, PrivacyLevel.FULL_DETAILS)
    assert result is not _EVENTS


def test_unknown_level_raises():
    class Bogus(str):
        pass

    with pytest.raises(ValueError):
        apply_filter(_EVENTS, Bogus("never"))  # type: ignore[arg-type]


def test_filter_handles_empty_input():
    assert apply_filter([], PrivacyLevel.FULL_DETAILS) == []
    assert apply_filter([], PrivacyLevel.BUSY_ONLY) == []
    assert apply_filter([], PrivacyLevel.DECISION_ONLY) == []
