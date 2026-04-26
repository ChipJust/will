"""Platform HTTP + WebSocket entry point."""
from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="agent-scheduling platform")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app
