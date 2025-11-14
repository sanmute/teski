from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user

from .models import NotificationPreference
from .schemas import NotificationPreferenceIn, NotificationPreferenceOut
from .service import (
    generate_notification_preview,
    get_or_create_preferences,
    upsert_preferences,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preview")
def notification_preview(
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    preview = generate_notification_preview(session, user.id)
    if preview is None:
        return {"available": False}
    return {"available": True, **preview.model_dump()}


@router.get("/preferences", response_model=NotificationPreferenceOut)
def get_preferences(
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> NotificationPreferenceOut:
    pref = get_or_create_preferences(session, user.id)
    return _preference_to_out(pref)


@router.post("/preferences", response_model=NotificationPreferenceOut)
def save_preferences(
    payload: NotificationPreferenceIn,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> NotificationPreferenceOut:
    pref = upsert_preferences(session, user.id, payload)
    return _preference_to_out(pref)


def _preference_to_out(pref: NotificationPreference) -> NotificationPreferenceOut:
    return NotificationPreferenceOut(
        id=pref.id,
        user_id=pref.user_id,
        enable_task_reminders=pref.enable_task_reminders,
        enable_review_reminders=pref.enable_review_reminders,
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
        max_per_day=pref.max_per_day,
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )
