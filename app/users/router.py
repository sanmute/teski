from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.models import User

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
