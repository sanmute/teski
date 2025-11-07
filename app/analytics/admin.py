from __future__ import annotations

from fastapi import APIRouter

from .jobs import nightly_analytics_job

router = APIRouter(prefix="/analytics/admin", tags=["analytics-admin"])


@router.post("/run-now")
def run_now() -> dict:
    return nightly_analytics_job()
