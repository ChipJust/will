"""Negotiator — per-user state machine for the agent-to-agent protocol.

LLM-free. Drives the protocol slice-by-slice; later slices add BATCH_SCHEDULE,
FREE_BUSY, PROPOSE, etc. on top of the HELLO scaffolding here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from agent_scheduling.adapters.base import Event, TimeWindow
from agent_scheduling.privacy import PrivacyPolicyStore, apply_filter
from agent_scheduling.protocol import Envelope, MessageType
from agent_scheduling.solver import MeetingRequest


def _event_to_dict(event: Event) -> dict:
    return {
        "title": event.title,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "attendees": list(event.attendees),
        "location": event.location,
    }


def _event_from_dict(data: dict) -> Event:
    return Event(
        title=data["title"],
        start=datetime.fromisoformat(data["start"]),
        end=datetime.fromisoformat(data["end"]),
        attendees=tuple(data.get("attendees", ())),
        location=data.get("location"),
    )


@dataclass
class Negotiator:
    agent_id: str
    user_id: str
    capabilities: list[str] = field(default_factory=list)
    clock: Callable[[], datetime] = field(default=datetime.now)

    _sequence_no: int = field(default=0, init=False)
    peers: dict[str, list[str]] = field(default_factory=dict, init=False)
    peer_free_busy: dict[str, list[Event]] = field(default_factory=dict, init=False)

    def hello(self, room_id: str, negotiation_id: str) -> Envelope:
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.HELLO,
            body={"capabilities": list(self.capabilities)},
        )

    def batch_schedule(
        self,
        room_id: str,
        negotiation_id: str,
        meetings: list[MeetingRequest],
        window_start: datetime,
        window_end: datetime,
    ) -> Envelope:
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.BATCH_SCHEDULE,
            body={
                "meetings": [
                    {
                        "name": m.name,
                        "participants": list(m.participants),
                        "duration_minutes": m.duration_minutes,
                    }
                    for m in meetings
                ],
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
            },
        )

    def free_busy(
        self,
        room_id: str,
        negotiation_id: str,
        viewer_user_id: str,
        events: list[Event],
        policy_store: PrivacyPolicyStore,
        window: TimeWindow,
    ) -> Envelope:
        """Emit a FREE_BUSY envelope filtered for one specific viewer.

        ADR 0004: directional per-edge privacy is applied at send time. To honor
        per-viewer policies in a multi-recipient room, the negotiator emits one
        FREE_BUSY message per peer (orchestration concern handled by the caller).
        """
        level = policy_store.get(subject=self.user_id, viewer=viewer_user_id)
        filtered = apply_filter(events, level)
        return Envelope(
            room_id=room_id,
            negotiation_id=negotiation_id,
            sender_agent_id=self.agent_id,
            sender_user_id=self.user_id,
            sequence_no=self._next_seq(),
            timestamp=self.clock(),
            message_type=MessageType.FREE_BUSY,
            body={
                "viewer_user_id": viewer_user_id,
                "events": [_event_to_dict(e) for e in filtered],
                "window_start": window.start.isoformat(),
                "window_end": window.end.isoformat(),
                "level": level.value,
            },
        )

    def receive(self, envelope: Envelope) -> None:
        if envelope.message_type == MessageType.HELLO:
            self.peers[envelope.sender_agent_id] = list(
                envelope.body.get("capabilities", [])
            )
        elif envelope.message_type == MessageType.FREE_BUSY:
            # Only ingest if this FREE_BUSY is addressed to us.
            if envelope.body.get("viewer_user_id") == self.user_id:
                self.peer_free_busy[envelope.sender_agent_id] = [
                    _event_from_dict(d) for d in envelope.body.get("events", [])
                ]

    def _next_seq(self) -> int:
        seq = self._sequence_no
        self._sequence_no += 1
        return seq
