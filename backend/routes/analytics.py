from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="", tags=["analytics"])


@router.get("/summary")
def summary():
    """Stub summary endpoint expected by frontend."""
    return {"ok": True, "summary": {}}


@router.get("/daily")
def daily(days: int = Query(default=7, ge=1, le=90)):
    """Stub daily analytics."""
    return {"ok": True, "days": days, "items": []}


@router.get("/by-course")
def by_course(days: int = Query(default=7, ge=1, le=90)):
    """Stub by-course analytics."""
    return {"ok": True, "days": days, "items": []}


@router.get("/insights")
def insights():
    """Stub insights analytics."""
    return {"ok": True, "items": []}

