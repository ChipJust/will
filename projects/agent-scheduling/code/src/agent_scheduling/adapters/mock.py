"""In-memory adapter for tests."""
from __future__ import annotations

from agent_scheduling.adapters.base import (
    Event,
    InviteResult,
    MeetingInvite,
    TimeWindow,
)


class MockAdapter:
    def __init__(self, events: list[Event] | None = None) -> None:
        self._events: list[Event] = list(events) if events else []
        self._sent: list[MeetingInvite] = []

    def list_calendar_events(self, window: TimeWindow) -> list[Event]:
        return [
            event
            for event in self._events
            if event.end > window.start and event.start < window.end
        ]

    def send_invite(self, invite: MeetingInvite) -> InviteResult:
        self._sent.append(invite)
        return InviteResult(success=True, invite_id=f"mock-{len(self._sent)}")

    @property
    def sent_invites(self) -> list[MeetingInvite]:
        return list(self._sent)
