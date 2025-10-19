# >>> MEMORY START
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.db import get_session
from backend.routes.deps import get_current_user
from backend.schemas_memory import LogMistakeIn, NextTasksOut, PlanBuildIn
from backend.services.memory import build_resurface_plan, fetch_next_resurfaced_instances, log_mistake

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


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
def next_tasks_endpoint(count: int = 3, session: Session = Depends(get_session), user=Depends(get_current_user)):
    items = fetch_next_resurfaced_instances(session, user_id=user.id, count=count)
    return {"items": items}
# <<< MEMORY END
