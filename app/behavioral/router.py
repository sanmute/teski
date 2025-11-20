from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, conint, confloat
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.models import PracticeSession, User
from app.behavioral.model import (
    get_behavior_profile,
    recommend_session_length,
    update_behavioral_profile,
)
from app.timeutil import _utcnow

router = APIRouter(prefix="/behavior", tags=["behavior"])


class PracticeSessionIn(BaseModel):
    user_id: UUID
    skill_id: Optional[UUID] = None
    length: conint(ge=1, le=20)
    correct_count: conint(ge=0)
    incorrect_count: conint(ge=0)
    avg_difficulty: confloat(ge=1, le=5) = 1.0
    fraction_review: confloat(ge=0, le=1) = 0.0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    abandoned: bool = False


class BehavioralProfileOut(BaseModel):
    engagement_level: float
    consistency_score: float
    challenge_preference: float
    review_vs_new_bias: float
    session_length_preference: float
    fatigue_risk: float
    suggested_length: int


@router.post("/session", status_code=status.HTTP_201_CREATED)
def log_practice_session(payload: PracticeSessionIn, db: Session = Depends(get_session)) -> dict[str, str]:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    started_at = payload.started_at or _utcnow()
    finished_at = payload.finished_at or _utcnow()
    session_row = PracticeSession(
        user_id=payload.user_id,
        skill_id=payload.skill_id,
        length=payload.length,
        correct_count=payload.correct_count,
        incorrect_count=payload.incorrect_count,
        avg_difficulty=payload.avg_difficulty,
        fraction_review=payload.fraction_review,
        started_at=started_at,
        finished_at=finished_at,
        abandoned=payload.abandoned,
    )
    db.add(session_row)
    profile = update_behavioral_profile(db, payload.user_id)
    db.commit()
    return {"status": "logged", "suggested_length": str(recommend_session_length(profile))}


@router.get("/profile", response_model=BehavioralProfileOut)
def get_profile(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> BehavioralProfileOut:
    profile = update_behavioral_profile(db, current_user.id)
    db.commit()
    return BehavioralProfileOut(
        engagement_level=profile.engagement_level,
        consistency_score=profile.consistency_score,
        challenge_preference=profile.challenge_preference,
        review_vs_new_bias=profile.review_vs_new_bias,
        session_length_preference=profile.session_length_preference,
        fatigue_risk=profile.fatigue_risk,
        suggested_length=recommend_session_length(profile),
    )
