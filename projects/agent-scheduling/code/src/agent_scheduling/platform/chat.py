"""Chat-room registry with optional SQLite persistence (slices 21–24)."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
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


class SqliteChatStore:
    """Append-only chat persistence keyed by room_id."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id, id)"
        )
        self._conn.commit()

    def append(self, room_id: str, message: dict) -> None:
        self._conn.execute(
            "INSERT INTO messages (room_id, payload) VALUES (?, ?)",
            (room_id, json.dumps(message)),
        )
        self._conn.commit()

    def history(self, room_id: str, limit: int = 100) -> list[dict]:
        cursor = self._conn.execute(
            "SELECT payload FROM messages WHERE room_id = ? ORDER BY id DESC LIMIT ?",
            (room_id, limit),
        )
        rows = cursor.fetchall()
        return [json.loads(row[0]) for row in reversed(rows)]

    def close(self) -> None:
        self._conn.close()


class RoomRegistry:
    def __init__(self, store: SqliteChatStore | None = None) -> None:
        self._rooms: dict[str, ChatRoom] = {}
        self._connections: dict[str, list[Any]] = {}
        self._store = store

    def get_or_create(self, room_id: str) -> ChatRoom:
        if room_id not in self._rooms:
            room = ChatRoom(room_id=room_id)
            if self._store is not None:
                room.history = self._store.history(room_id, room.history_limit)
            self._rooms[room_id] = room
        return self._rooms[room_id]

    def post(self, room_id: str, message: dict) -> None:
        room = self.get_or_create(room_id)
        room.post(message)
        if self._store is not None:
            self._store.append(room_id, message)

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
                self.unregister(room_id, websocket)
