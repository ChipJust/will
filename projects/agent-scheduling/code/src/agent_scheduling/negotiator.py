"""Negotiator — per-user state machine for the agent-to-agent protocol.

LLM-free. Drives the protocol slice-by-slice; later slices add BATCH_SCHEDULE,
FREE_BUSY, PROPOSE, etc. on top of the HELLO scaffolding here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from agent_scheduling.protocol import Envelope, MessageType
from agent_scheduling.solver import MeetingRequest


@dataclass
class Negotiator:
    agent_id: str
    user_id: str
    capabilities: list[str] = field(default_factory=list)
    clock: Callable[[], datetime] = field(default=datetime.now)

    _sequence_no: int = field(default=0, init=False)
    peers: dict[str, list[str]] = field(default_factory=dict, init=False)

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

    def receive(self, envelope: Envelope) -> None:
        if envelope.message_type == MessageType.HELLO:
            self.peers[envelope.sender_agent_id] = list(
                envelope.body.get("capabilities", [])
            )

    def _next_seq(self) -> int:
        seq = self._sequence_no
        self._sequence_no += 1
        return seq
