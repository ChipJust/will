"""Platform HTTP + WebSocket entry point."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from agent_scheduling.platform.chat import RoomRegistry, SqliteChatStore


VALID_KINDS = frozenset({"user", "agent"})


def create_app(db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="agent-scheduling platform")
    store = SqliteChatStore(db_path) if db_path is not None else None
    app.state.rooms = RoomRegistry(store=store)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.websocket("/ws/{room_id}")
    async def ws_endpoint(websocket: WebSocket, room_id: str) -> None:
        await websocket.accept()
        registry = app.state.rooms
        room = registry.get_or_create(room_id)
        for message in room.recent():
            await websocket.send_json(message)
        registry.register(room_id, websocket)
        try:
            while True:
                message = await websocket.receive_json()
                kind = message.get("kind") if isinstance(message, dict) else None
                if kind not in VALID_KINDS:
                    await websocket.send_json(
                        {
                            "error": "invalid_kind",
                            "message": f"'kind' must be one of {sorted(VALID_KINDS)}",
                        }
                    )
                    continue
                registry.post(room_id, message)
                await registry.broadcast(room_id, message)
        except WebSocketDisconnect:
            return
        finally:
            registry.unregister(room_id, websocket)

    return app
