"""In-memory adapter for tests."""
from __future__ import annotations

from agent_scheduling.adapters.base import (
    AdapterHealth,
    Event,
    InviteResult,
    MeetingInvite,
    TimeWindow,
)


class MockAdapter:
    def __init__(
        self,
        events: list[Event] | None = None,
        send_address: str = "mock@example.com",
        healthy: bool = True,
        health_error: str | None = None,
    ) -> None:
        self._events: list[Event] = list(events) if events else []
        self._sent: list[MeetingInvite] = []
        self._send_address = send_address
        self._healthy = healthy
        self._health_error = health_error

    def list_calendar_events(self, window: TimeWindow) -> list[Event]:
        return [
            event
            for event in self._events
            if event.end > window.start and event.start < window.end
        ]

    def send_invite(self, invite: MeetingInvite) -> InviteResult:
        self._sent.append(invite)
        return InviteResult(success=True, invite_id=f"mock-{len(self._sent)}")

    def get_send_address(self) -> str:
        return self._send_address

    def health(self) -> AdapterHealth:
        return AdapterHealth(ok=self._healthy, error=self._health_error)

    @property
    def sent_invites(self) -> list[MeetingInvite]:
        return list(self._sent)
