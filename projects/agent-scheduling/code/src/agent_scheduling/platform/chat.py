"""In-memory chat-room registry (slices 21+).

Messages are dicts. SQLite persistence is layered on in slice 24.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatRoom:
    room_id: str
    history: list[dict] = field(default_factory=list)
    history_limit: int = 100

    def post(self, message: dict) -> None:
        self.history.append(message)
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]

    def recent(self, limit: int | None = None) -> list[dict]:
        if limit is None:
            return list(self.history)
        return self.history[-limit:]


class RoomRegistry:
    def __init__(self) -> None:
        self._rooms: dict[str, ChatRoom] = {}

    def get_or_create(self, room_id: str) -> ChatRoom:
        if room_id not in self._rooms:
            self._rooms[room_id] = ChatRoom(room_id=room_id)
        return self._rooms[room_id]
