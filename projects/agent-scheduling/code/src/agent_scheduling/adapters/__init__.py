"""Email + calendar adapters (per ADR 0007).

One adapter per (user, provider). The agent picks which adapter to use per
meeting. First implementation: MockAdapter for tests; real Google adapter
follows in a later slice.
"""
from agent_scheduling.adapters.base import EmailCalendarAdapter, Event, TimeWindow
from agent_scheduling.adapters.mock import MockAdapter

__all__ = ["EmailCalendarAdapter", "Event", "TimeWindow", "MockAdapter"]
