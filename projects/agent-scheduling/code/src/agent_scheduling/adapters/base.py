"""Adapter Protocol + shared value types."""
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


@dataclass(frozen=True)
class MeetingInvite:
    title: str
    start: datetime
    end: datetime
    attendees: tuple[str, ...]
    location: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class InviteResult:
    success: bool
    invite_id: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class AdapterHealth:
    ok: bool
    error: str | None = None


class EmailCalendarAdapter(Protocol):
    def list_calendar_events(self, window: TimeWindow) -> list[Event]: ...
    def send_invite(self, invite: MeetingInvite) -> InviteResult: ...
    def get_send_address(self) -> str: ...
    def health(self) -> AdapterHealth: ...
