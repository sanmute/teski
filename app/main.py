from __future__ import annotations

from fastapi import FastAPI

from app.api import router as memory_router
from app.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="Teski Memory API", version="2.0")

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(memory_router)

    @app.on_event("startup")
    async def _startup() -> None:
        init_db()

    return app


app = create_app()
