from __future__ import annotations

import os

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

from app.api import router as memory_router
from app.ex_api import router as ex_router
from app.exams.api import exam_router
from app.db import init_db
from app.feedback.router import router as feedback_router
from app.analytics.admin import router as analytics_admin_router
from app.analytics.kpis import router as analytics_kpis_router
from app.analytics.jobs import nightly_analytics_job
from app.deep.router import router as deep_router
from app.prefs.router import router as prefs_router

ENABLE_ANALYTICS_JOBS = os.getenv("ENABLE_ANALYTICS_JOBS", "false").lower() in {"1", "true", "yes"}
ANALYTICS_CRON = os.getenv("ANALYTICS_CRON", "0 2 * * *")

_scheduler: BackgroundScheduler | None = None


def _build_cron_trigger(expr: str) -> CronTrigger:
    parts = expr.split()
    if len(parts) != 5:
        parts = "0 2 * * *".split()
    return CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        timezone="UTC",
    )


def _start_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
        trigger = _build_cron_trigger(ANALYTICS_CRON)
        _scheduler.add_job(
            nightly_analytics_job,
            trigger,
            id="teski_nightly_analytics",
            max_instances=1,
            replace_existing=True,
        )
        _scheduler.start()


def _stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def create_app() -> FastAPI:
    app = FastAPI(title="Teski Memory API", version="2.0")

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(memory_router)
    app.include_router(ex_router)
    app.include_router(exam_router)
    app.include_router(feedback_router)
    app.include_router(analytics_admin_router)
    app.include_router(analytics_kpis_router)
    app.include_router(deep_router)
    app.include_router(prefs_router)

    @app.on_event("startup")
    async def _startup() -> None:
        init_db()
        if ENABLE_ANALYTICS_JOBS:
            _start_scheduler()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        _stop_scheduler()

    return app


app = create_app()
