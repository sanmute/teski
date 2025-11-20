from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.deps import get_current_user
from app.models import User
from app.persona_reactions import PERSONA_CHOICES

router = APIRouter(prefix="/users", tags=["users"])


class AnalyticsConsentUpdate(BaseModel):
    analytics_consent: bool


@router.patch("/me/analytics-consent")
def update_analytics_consent(
    payload: AnalyticsConsentUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    current_user.analytics_consent = payload.analytics_consent
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"analytics_consent": current_user.analytics_consent}


class PersonaProfile(BaseModel):
    user_id: UUID
    persona: str
    available_personas: list[str]


class PersonaUpdateRequest(BaseModel):
    user_id: UUID
    persona: str


def _ensure_user(session: Session, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user:
        return user
    user = User(id=user_id, persona=get_settings().PERSONA_DEFAULT)
    session.add(user)
    session.flush()
    session.refresh(user)
    return user


@router.get("/persona", response_model=PersonaProfile)
def get_persona_profile(
    user_id: UUID = Query(...),
    session: Session = Depends(get_session),
) -> PersonaProfile:
    user = _ensure_user(session, user_id)
    persona = (user.persona or get_settings().PERSONA_DEFAULT).lower()
    return PersonaProfile(user_id=user.id, persona=persona, available_personas=PERSONA_CHOICES)


@router.post("/persona", response_model=PersonaProfile, status_code=status.HTTP_200_OK)
def update_persona_profile(
    payload: PersonaUpdateRequest,
    session: Session = Depends(get_session),
) -> PersonaProfile:
    persona_key = payload.persona.strip().lower()
    if persona_key not in PERSONA_CHOICES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_persona")
    user = _ensure_user(session, payload.user_id)
    user.persona = persona_key
    session.add(user)
    session.commit()
    session.refresh(user)
    return PersonaProfile(user_id=user.id, persona=user.persona, available_personas=PERSONA_CHOICES)
