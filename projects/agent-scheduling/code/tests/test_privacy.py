"""Tests for the directional privacy filter (slices 6 + 7)."""
from datetime import datetime

import pytest

from agent_scheduling.adapters.base import Event
from agent_scheduling.privacy import (
    DEFAULT_LEVEL,
    PrivacyLevel,
    PrivacyPolicyStore,
    apply_filter,
)


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


# Slice 7: PrivacyPolicyStore lookup


def test_default_level_is_decision_only():
    assert DEFAULT_LEVEL == PrivacyLevel.DECISION_ONLY


def test_unset_pair_returns_default():
    store = PrivacyPolicyStore()
    assert store.get(subject="alice", viewer="bob") == DEFAULT_LEVEL


def test_set_then_get_returns_set_value():
    store = PrivacyPolicyStore()
    store.set(subject="alice", viewer="bob", level=PrivacyLevel.FULL_DETAILS)
    assert store.get(subject="alice", viewer="bob") == PrivacyLevel.FULL_DETAILS


def test_policies_are_directional():
    """Asymmetry is by design — alice may share more with bob than bob shares with alice."""
    store = PrivacyPolicyStore()
    store.set(subject="alice", viewer="bob", level=PrivacyLevel.FULL_DETAILS)
    store.set(subject="bob", viewer="alice", level=PrivacyLevel.BUSY_ONLY)
    assert store.get(subject="alice", viewer="bob") == PrivacyLevel.FULL_DETAILS
    assert store.get(subject="bob", viewer="alice") == PrivacyLevel.BUSY_ONLY


def test_setting_one_pair_does_not_affect_others():
    store = PrivacyPolicyStore()
    store.set(subject="alice", viewer="bob", level=PrivacyLevel.FULL_DETAILS)
    assert store.get(subject="alice", viewer="carol") == DEFAULT_LEVEL
    assert store.get(subject="dave", viewer="bob") == DEFAULT_LEVEL


def test_setting_overwrites_previous_value():
    store = PrivacyPolicyStore()
    store.set(subject="alice", viewer="bob", level=PrivacyLevel.FULL_DETAILS)
    store.set(subject="alice", viewer="bob", level=PrivacyLevel.BUSY_ONLY)
    assert store.get(subject="alice", viewer="bob") == PrivacyLevel.BUSY_ONLY
