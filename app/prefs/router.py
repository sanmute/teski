from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..db import get_session
from .models import UserPrefs
from .schemas import PrefsIn, PrefsOut

router = APIRouter(prefix="/prefs", tags=["user-preferences"])


def _ensure(session: Session, user_id: UUID) -> UserPrefs:
    row = session.exec(select(UserPrefs).where(UserPrefs.user_id == user_id)).first()
    if row is None:
        row = UserPrefs(user_id=user_id)
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


@router.get("/get", response_model=PrefsOut)
def get_prefs(user_id: UUID, session: Session = Depends(get_session)) -> PrefsOut:
    row = _ensure(session, user_id)
    return PrefsOut(**row.model_dump())


@router.post("/set", response_model=PrefsOut)
def set_prefs(payload: PrefsIn, session: Session = Depends(get_session)) -> PrefsOut:
    row = _ensure(session, payload.user_id)
    data = payload.model_dump(exclude_unset=True)
    data.pop("user_id", None)
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return PrefsOut(**row.model_dump())
