from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel, select

from db import get_session
from models import User
from models_onboarding import UserOnboarding
from routes.deps import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingAnswers(SQLModel):
    motivation_style: Literal["mentor", "coach", "mixed"] = "mentor"
    difficulty_preference: Literal["gentle", "balanced", "hard"] = "balanced"
    daily_minutes_target: int = 15
    preferred_study_time: Literal["morning", "afternoon", "evening", "varies"] = "varies"
    focus_domains: List[str] = []
    notifications_opt_in: bool = False
    language: Optional[Literal["en", "fi", "sv"]] = None
    skipped: bool = False


@router.get("/status")
def onboarding_status(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Refresh from DB to avoid stale value
    user = session.get(User, current_user.id)
    return {"ok": True, "onboarded": bool(user.onboarded)}


@router.get("/me")
def onboarding_me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    answers = (
        session.exec(
            select(UserOnboarding).where(UserOnboarding.user_id == current_user.external_user_id).order_by(UserOnboarding.created_at.desc())
        ).first()
    )
    return {
        "ok": True,
        "onboarded": bool(current_user.onboarded),
        "answers": answers.answers if answers else None,
        "skipped": answers.skipped if answers else False,
    }


@router.post("/submit")
def onboarding_submit(
    payload: OnboardingAnswers,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Basic guard
    if payload.daily_minutes_target < 5 or payload.daily_minutes_target > 240:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="daily_minutes_target must be between 5 and 240",
        )

    record = UserOnboarding(
        user_id=current_user.external_user_id,
        answers=payload.model_dump(),
        skipped=payload.skipped,
        created_at=datetime.utcnow(),
    )
    session.add(record)

    # Mark user as onboarded
    current_user.onboarded = True
    current_user.onboarded_at = datetime.utcnow()
    session.add(current_user)

    session.commit()

    return {"ok": True, "onboarded": True}
