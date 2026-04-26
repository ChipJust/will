"""In-memory adapter for tests."""
from __future__ import annotations

from agent_scheduling.adapters.base import Event, TimeWindow


class MockAdapter:
    def __init__(self, events: list[Event] | None = None) -> None:
        self._events: list[Event] = list(events) if events else []

    def list_calendar_events(self, window: TimeWindow) -> list[Event]:
        return [
            event
            for event in self._events
            if event.end > window.start and event.start < window.end
        ]
