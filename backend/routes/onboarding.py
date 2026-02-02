from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, SQLModel, select

from db import get_session
from models import User
from models_onboarding import UserOnboarding, StudyProfile, StudyProfileV1
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


class StudyProfileIn(SQLModel):
    goal_primary: str
    time_budget: int
    intensity: Literal["light", "moderate", "intense"]
    focus_subjects: List[str]
    confidence: Optional[int] = None


class StudyProfileOut(StudyProfileIn):
    user_id: str
    has_profile: bool
    profile_version: int
    completed: bool
    created_at: datetime
    updated_at: datetime
    derived: Dict[str, Any]


@router.get("/status")
def onboarding_status(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        user = session.get(User, current_user.id)
        onboarded = bool(user.onboarded) if user else False
        return {"ok": True, "onboarded": onboarded, "user_id": current_user.id}
    except Exception as e:
        # Launch-safe: never bubble 500 for status
        return {"ok": False, "onboarded": False, "error": str(e), "user_id": current_user.id}


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


# --- Study Profile (minimal) ---

def _load_study_profile(session: Session, user_id: str) -> StudyProfile | None:
    return session.exec(select(StudyProfile).where(StudyProfile.user_id == user_id)).first()


def _load_study_profile_v1(session: Session, user_id: str) -> StudyProfileV1 | None:
    return session.exec(select(StudyProfileV1).where(StudyProfileV1.user_id == user_id).order_by(StudyProfileV1.id.desc())).first()


def _serialize_profile_v1(profile: StudyProfileV1) -> StudyProfileOut:
    payload = profile.profile_json or {}
    return StudyProfileOut(
        user_id=profile.user_id,
        has_profile=True,
        profile_version=profile.profile_version,
        completed=bool(profile.completed_at),
        goal_primary=payload.get("goal_primary"),
        time_budget=payload.get("time_budget"),
        intensity=payload.get("intensity"),
        focus_subjects=payload.get("focus_subjects", []),
        confidence=payload.get("confidence"),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        derived=_derive_settings(payload),
    )


@router.get("/profile", response_model=StudyProfileOut)
def get_study_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rid = getattr(request.state, "request_id", "n/a")
    try:
        profile = _load_study_profile_v1(session, current_user.external_user_id)
        if profile:
            return _serialize_profile_v1(profile)
        # defaults
        now = datetime.utcnow()
        payload = {
            "goal_primary": None,
            "time_budget": None,
            "intensity": None,
            "focus_subjects": [],
            "confidence": None,
        }
        return StudyProfileOut(
            user_id=current_user.external_user_id,
            has_profile=False,
            profile_version=1,
            completed=False,
            goal_primary=None,
            time_budget=None,
            intensity=None,
            focus_subjects=[],
            confidence=None,
            created_at=now,
            updated_at=now,
            derived=_derive_settings(payload),
        )
    except Exception:
        import traceback

        logging.exception(
            "onboarding.profile failed",
            extra={"request_id": rid, "user_id": getattr(current_user, "id", None), "external_user_id": getattr(current_user, "external_user_id", None)},
        )
        if request.headers.get("x-teski-debug") == "trace":
            # Let the global middleware surface full traceback and headers
            raise
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": rid},
        )


@router.post("/profile", response_model=StudyProfileOut)
def upsert_study_profile(
    payload: StudyProfileIn,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    profile = _load_study_profile_v1(session, current_user.external_user_id)
    now = datetime.utcnow()
    data = payload.model_dump()
    if profile:
        profile.profile_json = data
        profile.updated_at = now
        profile.completed_at = now
        session.add(profile)
    else:
        profile = StudyProfileV1(
            user_id=current_user.external_user_id,
            profile_version=1,
            profile_json=data,
            created_at=now,
            updated_at=now,
            completed_at=now,
        )
        session.add(profile)

    session.commit()
    session.refresh(profile)
    return _serialize_profile_v1(profile)
