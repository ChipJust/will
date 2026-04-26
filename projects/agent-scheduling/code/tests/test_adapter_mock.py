"""Tests for MockAdapter (slice 3+)."""
from datetime import datetime

from agent_scheduling.adapters import Event, MockAdapter, TimeWindow


def _dt(hour: int) -> datetime:
    return datetime(2026, 5, 1, hour, 0)


# Slice 3: list_calendar_events


def test_mock_adapter_returns_events_inside_window():
    inside = Event(title="standup", start=_dt(9), end=_dt(10))
    adapter = MockAdapter(events=[inside])
    window = TimeWindow(start=_dt(8), end=_dt(12))
    assert adapter.list_calendar_events(window) == [inside]


def test_mock_adapter_filters_events_outside_window():
    before = Event(title="early", start=_dt(6), end=_dt(7))
    inside = Event(title="standup", start=_dt(9), end=_dt(10))
    after = Event(title="late", start=_dt(20), end=_dt(21))
    adapter = MockAdapter(events=[before, inside, after])
    window = TimeWindow(start=_dt(8), end=_dt(12))
    assert adapter.list_calendar_events(window) == [inside]


def test_mock_adapter_includes_partial_overlap():
    overlap = Event(title="long", start=_dt(7), end=_dt(11))
    adapter = MockAdapter(events=[overlap])
    window = TimeWindow(start=_dt(9), end=_dt(10))
    assert adapter.list_calendar_events(window) == [overlap]


def test_mock_adapter_excludes_event_touching_window_edge():
    touching_start = Event(title="touches start", start=_dt(6), end=_dt(8))
    touching_end = Event(title="touches end", start=_dt(12), end=_dt(13))
    adapter = MockAdapter(events=[touching_start, touching_end])
    window = TimeWindow(start=_dt(8), end=_dt(12))
    assert adapter.list_calendar_events(window) == []


def test_mock_adapter_empty_calendar():
    adapter = MockAdapter(events=[])
    window = TimeWindow(start=_dt(0), end=_dt(23))
    assert adapter.list_calendar_events(window) == []


def test_mock_adapter_default_constructor_is_empty():
    adapter = MockAdapter()
    window = TimeWindow(start=_dt(0), end=_dt(23))
    assert adapter.list_calendar_events(window) == []
