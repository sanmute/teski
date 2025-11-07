from __future__ import annotations

import os

from fastapi import FastAPI

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

from app.api import router as memory_router
from app.ex_api import router as ex_router
from app.exams.api import exam_router
from app.db import init_db
from app.feedback.router import router as feedback_router


def create_app() -> FastAPI:
    app = FastAPI(title="Teski Memory API", version="2.0")

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(memory_router)
    app.include_router(ex_router)
    app.include_router(exam_router)
    app.include_router(feedback_router)

    @app.on_event("startup")
    async def _startup() -> None:
        init_db()

    return app


app = create_app()
