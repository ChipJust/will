"""Platform HTTP + WebSocket entry point."""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from agent_scheduling.platform.chat import RoomRegistry


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
                room.post(message)
                await websocket.send_json(message)
        except WebSocketDisconnect:
            return

    return app
