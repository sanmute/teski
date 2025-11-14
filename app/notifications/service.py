from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.learner.models import LearnerProfile
from app.learner.service import get_or_default_profile
from app.models import _utcnow
from app.tasks.models import Task, TaskBlock
from app.tasks.service import compute_personalized_minutes

from .models import NotificationPreference
from .schemas import NotificationPreferenceIn, NotificationPreview

FOCUS_WINDOWS = {
    "morning": (8, 11),
    "afternoon": (12, 16),
    "evening": (17, 21),
    "late_night": (21, 24),
}

TONE_TEMPLATES = {
    "short": "Time to work on '{title}' for about {minutes} minutes.",
    "normal": "You planned to work on '{title}'. Let's spend about {minutes} minutes on it.",
    "supportive": "Let's take a {minutes}-minute step on '{title}' — I’ll keep it manageable.",
    "strict": "Start '{title}' now. {minutes} minutes. No postponing.",
    "detailed": "We'll kick off '{title}' with a {minutes}-minute {label}, tailored to your study style.",
}


def get_or_create_preferences(session: Session, user_id: UUID) -> NotificationPreference:
    pref = session.exec(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    ).first()
    if pref is None:
        pref = NotificationPreference(user_id=user_id)
        session.add(pref)
        session.commit()
        session.refresh(pref)
    return pref


def upsert_preferences(
    session: Session, user_id: UUID, payload: NotificationPreferenceIn
) -> NotificationPreference:
    pref = get_or_create_preferences(session, user_id)
    for field, value in payload.model_dump().items():
        setattr(pref, field, value)
    pref.updated_at = _utcnow()
    session.add(pref)
    session.commit()
    session.refresh(pref)
    return pref


def generate_notification_preview(session: Session, user_id: UUID) -> Optional[NotificationPreview]:
    profile = get_or_default_profile(session, user_id)
    pref = get_or_create_preferences(session, user_id)
    if not pref.enable_task_reminders:
        return None

    task = _next_relevant_task(session, user_id)
    if task is None:
        return None

    blocks = session.exec(
        select(TaskBlock).where(TaskBlock.task_id == task.id).order_by(TaskBlock.created_at)
    ).all()
    duration = blocks[0].duration_minutes if blocks else compute_personalized_minutes(task, profile)
    label = blocks[0].label if blocks else "focus block"
    message = _render_message(profile, task.title, duration, label)
    suggested_time = _suggest_time(profile.focus_time)
    return NotificationPreview(message=message, task_id=task.id, suggested_time=suggested_time)


def _next_relevant_task(session: Session, user_id: UUID) -> Task | None:
    stmt = (
        select(Task)
        .where(Task.user_id == user_id, Task.status == "pending")
        .order_by(func.coalesce(Task.due_at, Task.created_at))
    )
    return session.exec(stmt).first()


def _render_message(profile: LearnerProfile, title: str, minutes: int, label: str) -> str:
    tone = profile.communication_style or "normal"
    template = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["normal"])
    return template.format(title=title, minutes=minutes, label=label.lower())


def _suggest_time(focus_time: Optional[str]) -> datetime:
    window = FOCUS_WINDOWS.get(focus_time or "", None)
    now = _utcnow()
    if not window:
        return now
    start_hour, end_hour = window
    start_today = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if now.hour < start_hour:
        return start_today
    if start_hour <= now.hour < end_hour:
        return now
    return start_today + timedelta(days=1)
