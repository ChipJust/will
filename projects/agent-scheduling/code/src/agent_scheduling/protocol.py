"""Agent-to-agent protocol envelope (per spec section "Agent-to-agent protocol").

Every message between agents is wrapped in `Envelope`. The body schema varies
per `message_type` and is filled in as later slices drive out each message.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    HELLO = "HELLO"
    BATCH_SCHEDULE = "BATCH_SCHEDULE"
    FREE_BUSY = "FREE_BUSY"
    PROPOSE = "PROPOSE"
    ACCEPT = "ACCEPT"
    COUNTER = "COUNTER"
    DECLINE = "DECLINE"
    CONFIRM = "CONFIRM"
    DEADLOCK_ASK = "DEADLOCK_ASK"
    DEADLOCK_RELAX = "DEADLOCK_RELAX"


@dataclass(frozen=True)
class Envelope:
    room_id: str
    negotiation_id: str
    sender_agent_id: str
    sender_user_id: str
    sequence_no: int
    timestamp: datetime
    message_type: MessageType
    body: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "room_id": self.room_id,
                "negotiation_id": self.negotiation_id,
                "sender_agent_id": self.sender_agent_id,
                "sender_user_id": self.sender_user_id,
                "sequence_no": self.sequence_no,
                "timestamp": self.timestamp.isoformat(),
                "message_type": self.message_type.value,
                "body": self.body,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> Envelope:
        parsed = json.loads(data)
        return cls(
            room_id=parsed["room_id"],
            negotiation_id=parsed["negotiation_id"],
            sender_agent_id=parsed["sender_agent_id"],
            sender_user_id=parsed["sender_user_id"],
            sequence_no=parsed["sequence_no"],
            timestamp=datetime.fromisoformat(parsed["timestamp"]),
            message_type=MessageType(parsed["message_type"]),
            body=parsed.get("body", {}),
        )
