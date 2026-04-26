"""Email + calendar adapters (per ADR 0007).

One adapter per (user, provider). The agent picks which adapter to use per
meeting. First implementation: MockAdapter for tests; real Google adapter
follows in a later slice.
"""
from agent_scheduling.adapters.base import (
    AdapterHealth,
    EmailCalendarAdapter,
    Event,
    InviteResult,
    MeetingInvite,
    TimeWindow,
)
from agent_scheduling.adapters.mock import MockAdapter

__all__ = [
    "AdapterHealth",
    "EmailCalendarAdapter",
    "Event",
    "InviteResult",
    "MeetingInvite",
    "MockAdapter",
    "TimeWindow",
]
