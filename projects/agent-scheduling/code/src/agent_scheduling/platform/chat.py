"""In-memory chat-room registry (slices 21+).

Messages are dicts. SQLite persistence is layered on in slice 24.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
        self._connections: dict[str, list[Any]] = {}

    def get_or_create(self, room_id: str) -> ChatRoom:
        if room_id not in self._rooms:
            self._rooms[room_id] = ChatRoom(room_id=room_id)
        return self._rooms[room_id]

    def register(self, room_id: str, websocket: Any) -> None:
        self._connections.setdefault(room_id, []).append(websocket)

    def unregister(self, room_id: str, websocket: Any) -> None:
        connections = self._connections.get(room_id, [])
        if websocket in connections:
            connections.remove(websocket)

    async def broadcast(self, room_id: str, message: dict) -> None:
        for websocket in list(self._connections.get(room_id, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                # Stale connection — drop it.
                self.unregister(room_id, websocket)
