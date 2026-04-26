"""Directional per-edge privacy filter (ADR 0004).

`apply_filter` strips event metadata according to the configured privacy level
between a (subject, viewer) pair. Levels:

  full_details   — passthrough of events.
  busy_only      — time slots only; title becomes "busy"; attendees/location dropped.
  decision_only  — at this slice, equivalent to busy_only. A later slice will
                   further narrow to "acceptable for this meeting" when negotiation
                   context is available.

`PrivacyPolicyStore` holds per-(subject, viewer) policies. Default for unset
pairs is the most-restrictive useful level: decision_only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from agent_scheduling.adapters.base import Event


class PrivacyLevel(str, Enum):
    FULL_DETAILS = "full_details"
    DECISION_ONLY = "decision_only"
    BUSY_ONLY = "busy_only"


DEFAULT_LEVEL = PrivacyLevel.DECISION_ONLY


def apply_filter(events: list[Event], level: PrivacyLevel) -> list[Event]:
    if level == PrivacyLevel.FULL_DETAILS:
        return list(events)
    if level in (PrivacyLevel.BUSY_ONLY, PrivacyLevel.DECISION_ONLY):
        return [
            Event(title="busy", start=e.start, end=e.end, attendees=(), location=None)
            for e in events
        ]
    raise ValueError(f"Unknown privacy level: {level}")


@dataclass
class PrivacyPolicyStore:
    """Per-(subject, viewer) policy lookup. Directional and asymmetric by design."""

    _policies: dict[tuple[str, str], PrivacyLevel] = field(default_factory=dict)

    def set(self, subject: str, viewer: str, level: PrivacyLevel) -> None:
        self._policies[(subject, viewer)] = level

    def get(self, subject: str, viewer: str) -> PrivacyLevel:
        return self._policies.get((subject, viewer), DEFAULT_LEVEL)
