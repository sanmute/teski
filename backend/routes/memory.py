# >>> MEMORY START
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from db import get_session
from routes.deps import get_current_user
from schemas_memory import LogMistakeIn, NextTasksOut, PlanBuildIn
from services.memory import build_resurface_plan, fetch_next_resurfaced_instances, log_mistake

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/log", response_model=dict)
def log_mistake_endpoint(
    payload: LogMistakeIn, session: Session = Depends(get_session), user=Depends(get_current_user)
):
    record = log_mistake(
        session,
        user_id=user.id,
        skill_id=payload.skill_id,
        template_code=payload.template_code,
        instance_id=payload.instance_id,
        error_type=payload.error_type,
        detail=payload.detail,
    )
    return {"id": record.id}


@router.post("/plan", response_model=dict)
def build_plan_endpoint(
    payload: PlanBuildIn, session: Session = Depends(get_session), user=Depends(get_current_user)
):
    scheduled = build_resurface_plan(
        session, user_id=user.id, count=payload.count, horizon_minutes=payload.horizon_minutes
    )
    return {"scheduled": len(scheduled)}


@router.get("/next", response_model=NextTasksOut)
def next_tasks_endpoint(
    limit: int = Query(default=3, ge=1, le=100, alias="limit"),
    user_id: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    """
    Accepts user_id as a UUID/string (front-end sends UUID). If user_id cannot
    be coerced to an int for the legacy memory tables, return an empty list
    rather than a 422/500.
    """
    if user_id is None:
        return {"items": []}
    try:
        legacy_user_id = int(user_id)
    except (TypeError, ValueError):
        return {"items": []}

    items = fetch_next_resurfaced_instances(session, user_id=legacy_user_id, count=limit)
    return {"items": items}
# <<< MEMORY END
