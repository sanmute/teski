from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.abtest import assign_and_persist
from app.analytics import log as log_event
from app.badges import check_nemesis
from app.config import get_settings
from app.db import get_session
from app.detectors import classify_mistake
from app.exercises import load_exercises
from app.models import AnalyticsEvent, MemoryItem, Mistake, MistakeSubtype, ReviewLog, User
from app.personas import get_persona_copy
from app.timeutil import user_day_bounds
from app.scheduler import enforce_daily_cap, get_next_reviews, review as review_memory, schedule_from_mistake
from app.schemas import (
    AssignABIn,
    MistakeIn,
    MistakeOut,
    NextReviewItem,
    NextReviewOut,
    PersonaOut,
    ReviewIn,
    ReviewOut,
    StatsOut,
)
from app.xp import award as award_xp

router = APIRouter(prefix="/memory", tags=["memory-v2"])


def _ensure_enabled() -> None:
    if get_settings().KILL_SWITCH:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Memory service temporarily disabled")


def _ensure_user(session: Session, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user:
        return user
    user = User(id=user_id, created_at=datetime.utcnow(), timezone="UTC", streak_days=0, persona=get_settings().PERSONA_DEFAULT)
    session.add(user)
    session.flush()
    return user


@router.post("/mistake", response_model=MistakeOut, dependencies=[Depends(_ensure_enabled)])
def log_mistake(payload: MistakeIn, session: Session = Depends(get_session)) -> MistakeOut:
    user = _ensure_user(session, payload.user_id)
    concept = payload.concept.strip() or "unknown"
    context: Dict[str, object] = dict(payload.context or {})

    subtype = classify_mistake(
        prompt_text=str(context.get("prompt", "")),
        user_answer=payload.raw,
        correct_answer=str(context.get("correct", "")),
        context=context,
    )
    memory = schedule_from_mistake(session, user=user, concept=concept, task_id=payload.task_id)
    try:
        subtype_enum = MistakeSubtype(subtype)
        subtype = subtype_enum.value
    except ValueError:
        subtype_enum = MistakeSubtype.OTHER
        subtype = subtype_enum.value
    mistake = Mistake(
        user_id=user.id,
        task_id=payload.task_id,
        concept=concept,
        subtype=subtype_enum,
        raw=payload.raw or "",
    )
    session.add(mistake)
    award_xp(user, reason="mistake", base=3, mastery_bonus=0, session=session)
    log_event("memory.mistake_logged", {"concept": concept, "subtype": subtype}, user, session=session)
    session.commit()
    return MistakeOut(memory_id=memory.id, concept=concept, subtype=subtype)


@router.get("/next", response_model=NextReviewOut, dependencies=[Depends(_ensure_enabled)])
def next_reviews(
    user_id: UUID = Query(..., description="User identifier"),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session),
) -> NextReviewOut:
    user = _ensure_user(session, user_id)
    items = get_next_reviews(session, user=user, limit=limit)
    payload = [NextReviewItem(memory_id=item.id, concept=item.concept, due_at=item.due_at) for item in items]
    remaining = _remaining_today(session, user)
    log_event("memory.review_fetch", {"count": len(payload)}, user, session=session)
    return NextReviewOut(items=payload, remaining_today=remaining)


@router.post("/review", response_model=ReviewOut, dependencies=[Depends(_ensure_enabled)])
def submit_review(payload: ReviewIn, session: Session = Depends(get_session)) -> ReviewOut:
    user = _ensure_user(session, payload.user_id)
    memory = session.get(MemoryItem, payload.memory_id)
    if not memory or memory.user_id != user.id:
        raise HTTPException(status_code=404, detail="memory_not_found")

    updated = review_memory(session, user, memory, payload.grade)
    xp_awarded = award_xp(user, reason="review", memory=updated, session=session)
    check_nemesis(user, updated.concept, session=session)

    warmup = _today_review_count(session, user) == 0
    persona_msg = get_persona_copy(user.persona or get_settings().PERSONA_DEFAULT, {
        "warmup": warmup,
        "concept": updated.concept,
        "grade": payload.grade,
        "user_id": str(user.id),
    })
    log_event("memory.review_logged", {"concept": updated.concept, "grade": payload.grade, "xp": xp_awarded}, user, session=session)
    session.commit()

    return ReviewOut(
        memory_id=updated.id,
        concept=updated.concept,
        next_due_at=updated.due_at,
        interval_days=updated.interval,
        ease=updated.ease,
        xp_awarded=xp_awarded,
        persona_msg=persona_msg,
    )


@router.get("/persona", response_model=PersonaOut, dependencies=[Depends(_ensure_enabled)])
def persona_endpoint(user_id: UUID, session: Session = Depends(get_session)) -> PersonaOut:
    user = _ensure_user(session, user_id)
    warmup = _today_review_count(session, user) == 0
    copy = get_persona_copy(user.persona, {"warmup": warmup, "user_id": str(user.id)})
    return PersonaOut(user_id=user.id, persona=user.persona, warmup=warmup, copy=copy, warmup_ts=user.created_at)


@router.get("/stats", response_model=StatsOut, dependencies=[Depends(_ensure_enabled)])
def stats_endpoint(user_id: UUID, session: Session = Depends(get_session)) -> StatsOut:
    user = _ensure_user(session, user_id)
    today_count = _today_review_count(session, user)
    due_count = session.exec(
        select(func.count()).select_from(MemoryItem).where(
            MemoryItem.user_id == user.id,
            MemoryItem.due_at <= datetime.utcnow(),
        )
    ).one()
    if isinstance(due_count, tuple):
        due_count = due_count[0]
    due_count = int(due_count or 0)
    ex_correct, ex_incorrect = _today_exercise_counts(session, user)
    suggested = _suggested_exercises(user)
    settings = get_settings()
    return StatsOut(
        user_id=user.id,
        today_reviewed=today_count,
        daily_cap=settings.DAILY_REVIEW_CAP,
        streak_days=user.streak_days,
        due_count=due_count,
        exercises_correct_today=ex_correct,
        exercises_incorrect_today=ex_incorrect,
        suggested_new_exercises=suggested,
    )


@router.post("/ab/assign", dependencies=[Depends(_ensure_enabled)])
def assign_ab(payload: AssignABIn, session: Session = Depends(get_session)) -> Dict[str, str]:
    bucket = assign_and_persist(session, payload.user_id, payload.experiment)
    session.commit()
    return {"bucket": bucket}


def _today_review_count(session: Session, user: User) -> int:
    start, end = user_day_bounds(user.timezone)
    result = session.exec(
        select(func.count()).select_from(ReviewLog).where(
            ReviewLog.user_id == user.id,
            ReviewLog.reviewed_at >= start,
            ReviewLog.reviewed_at < end,
        )
    ).one()
    if isinstance(result, tuple):
        result = result[0]
    return int(result or 0)


def _remaining_today(session: Session, user: User) -> int:
    settings = get_settings()
    reviewed = _today_review_count(session, user)
    remaining = max(0, settings.DAILY_REVIEW_CAP - reviewed)
    return remaining


def _today_exercise_counts(session: Session, user: User) -> tuple[int, int]:
    start, end = user_day_bounds(user.timezone)
    correct = session.exec(
        select(func.count()).where(
            AnalyticsEvent.user_id == user.id,
            AnalyticsEvent.kind == "exercise_correct",
            AnalyticsEvent.ts >= start,
            AnalyticsEvent.ts < end,
        )
    ).one()
    incorrect = session.exec(
        select(func.count()).where(
            AnalyticsEvent.user_id == user.id,
            AnalyticsEvent.kind == "exercise_incorrect",
            AnalyticsEvent.ts >= start,
            AnalyticsEvent.ts < end,
        )
    ).one()
    if isinstance(correct, tuple):
        correct = correct[0]
    if isinstance(incorrect, tuple):
        incorrect = incorrect[0]
    return int(correct or 0), int(incorrect or 0)


def _suggested_exercises(user: User) -> int:
    exercises = load_exercises()
    if user.display_name:  # placeholder for course preference later
        return len(exercises)
    return len(exercises)
