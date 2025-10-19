# >>> MEMORY V1 START
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.db import get_session
from backend.routes.deps import get_current_user
from backend.utils.analytics import emit
from backend.models_memory import MistakeLog
from backend.schemas_memory import (
    BuildReviewsIn,
    LogMistakeInV1,
    ReviewItemOut,
    WarmupOut,
)
from backend.services.memory_v1 import (
    build_reviews,
    fetch_due_reviews,
    log_mistake_v1,
    mark_review_result,
)
from app.abtest import assign as assign_bucket
from app.analytics import log as log_event
from app.personas import get_persona_copy

try:
    from backend.services.persona import get_persona
except Exception:  # pragma: no cover - optional dependency
    get_persona = None

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.post("/log/v1", response_model=dict)
def log_mistake_endpoint_v1(
    payload: LogMistakeInV1, session: Session = Depends(get_session), user=Depends(get_current_user)
) -> dict:
    record = log_mistake_v1(
        session,
        user_id=user.id,
        skill_id=payload.skill_id,
        template_code=payload.template_code,
        instance_id=payload.instance_id,
        error_type=payload.error_type,
        error_subtype=payload.error_subtype,
        detail=payload.detail,
    )
    return {"id": record.id}


@router.post("/review/build", response_model=dict)
def build_reviews_endpoint(
    payload: BuildReviewsIn, session: Session = Depends(get_session), user=Depends(get_current_user)
) -> dict:
    updated = build_reviews(
        session,
        user_id=user.id,
        max_new=payload.max_new,
        horizon_minutes=payload.horizon_minutes,
    )
    return {"scheduled_or_adjusted": updated}


@router.get("/review/next", response_model=WarmupOut)
def next_reviews_endpoint(
    count: int = 2, session: Session = Depends(get_session), user=Depends(get_current_user)
) -> WarmupOut:
    if assign_bucket(user, "memory_v1") == "B":
        emit("memory.review_shown", user.id, {"count": 0})
        log_event("memory.review_shown", {"count": 0, "bucket": "B"}, user)
        return WarmupOut(items=[])

    items = fetch_due_reviews(session, user_id=user.id, count=count)
    mood_code = getattr(user, "persona_code", None) or "mood_calm_v1"
    if get_persona and getattr(user, "persona_code", None):
        try:
            persona_obj = get_persona(session, user.persona_code)
            if persona_obj and isinstance(persona_obj.config, dict):
                mood_code = persona_obj.config.get("memoryMood", mood_code) or mood_code
        except Exception:
            pass
    def _persona_name(code: str) -> str:
        code = (code or "").lower()
        if "snark" in code:
            return "Snark"
        if "coach" in code:
            return "Coach"
        if "encour" in code:
            return "Encourager"
        return "Calm"

    persona_name = _persona_name(mood_code)
    for idx, item in enumerate(items):
        tpl_code = item.get("template_code")
        if not tpl_code:
            continue
        stmt = (
            select(MistakeLog)
            .where(
                MistakeLog.user_id == user.id,
                MistakeLog.template_code == tpl_code,
            )
            .order_by(MistakeLog.occurred_at.desc())
            .limit(1)
        )
        last = session.exec(stmt).first()
        subtype = getattr(last, "error_subtype", None) if last else None
        context = {
            "warmup": idx == 0,
            "concept": tpl_code,
            "user_id": user.id,
            "error_subtype": subtype,
        }
        item["prompt"] = get_persona_copy(persona_name, context)

    emit("memory.review_shown", user.id, {"count": len(items)})
    log_event("memory.review_shown", {"count": len(items), "bucket": "A"}, user)
    return WarmupOut(items=[ReviewItemOut(**item) for item in items])


@router.post("/review/result", response_model=dict)
def review_result_endpoint(
    template_code: str,
    correct: bool,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> dict:
    card = mark_review_result(session, user_id=user.id, template_code=template_code, correct=correct)
    if not card:
        raise HTTPException(status_code=404, detail="review_card_not_found")
    payload = {"template_code": template_code, "correct": bool(correct)}
    emit("memory.review_answered", user.id, payload)
    log_event("memory.review_answered", payload, user)
    return {
        "next_review_at": card.next_review_at.isoformat(),
        "easiness": card.easiness,
        "interval_days": card.last_interval_days,
    }
# <<< MEMORY V1 END
