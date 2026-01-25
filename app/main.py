from __future__ import annotations

import os

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
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
from app.analytics.investor_router import router as investor_analytics_router
from app.analytics.router import institution_router as analytics_institution_router
from app.analytics.router import router as analytics_me_router
from app.analytics.jobs import nightly_analytics_job
from app.deep.router import router as deep_router
from app.prefs.router import router as prefs_router
from app.pilot.router import router as pilot_router
from app.learner.router import router as onboarding_router
from app.tasks.router import router as tasks_router
from app.notifications.router import router as notifications_router
from app.explanations.router import router as explanations_router
from app.study.router import router as study_router
from app.integrations.moodle import router as moodle_router
from app.users.router import router as users_router
from app.reports.router import router as reports_router
from app.mastery.router import router as mastery_router
from app.behavioral.router import router as behavioral_router

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
    api_router = APIRouter(prefix="/api")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://teski.app",
            "https://www.teski.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    api_router.include_router(memory_router)
    api_router.include_router(ex_router)
    api_router.include_router(exam_router)
    api_router.include_router(feedback_router)
    api_router.include_router(analytics_admin_router)
    api_router.include_router(analytics_kpis_router)
    api_router.include_router(investor_analytics_router)
    api_router.include_router(analytics_institution_router)
    api_router.include_router(analytics_me_router)
    api_router.include_router(pilot_router)
    api_router.include_router(deep_router)
    api_router.include_router(prefs_router)
    api_router.include_router(tasks_router)
    api_router.include_router(notifications_router)
    api_router.include_router(explanations_router)
    api_router.include_router(onboarding_router)
    api_router.include_router(study_router)
    api_router.include_router(moodle_router)
    api_router.include_router(users_router)
    api_router.include_router(reports_router)
    api_router.include_router(mastery_router)
    api_router.include_router(behavioral_router)
    app.include_router(api_router)

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
