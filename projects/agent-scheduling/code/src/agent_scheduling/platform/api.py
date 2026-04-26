"""Platform HTTP + WebSocket entry point."""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from agent_scheduling.platform.chat import RoomRegistry


VALID_KINDS = frozenset({"user", "agent"})


def create_app() -> FastAPI:
    app = FastAPI(title="agent-scheduling platform")
    app.state.rooms = RoomRegistry()

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.websocket("/ws/{room_id}")
    async def ws_endpoint(websocket: WebSocket, room_id: str) -> None:
        await websocket.accept()
        room = app.state.rooms.get_or_create(room_id)
        for message in room.recent():
            await websocket.send_json(message)
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
                room.post(message)
                await websocket.send_json(message)
        except WebSocketDisconnect:
            return

    return app
