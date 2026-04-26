"""Adapter Protocol + shared value types.

The Protocol grows as slices drive out additional methods (send_invite, health,
get_send_address). At slice 3 only list_calendar_events is required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Event:
    title: str
    start: datetime
    end: datetime
    attendees: tuple[str, ...] = field(default_factory=tuple)
    location: str | None = None


class EmailCalendarAdapter(Protocol):
    def list_calendar_events(self, window: TimeWindow) -> list[Event]: ...
