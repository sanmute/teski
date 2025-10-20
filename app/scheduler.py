from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.config import get_settings
from app.models import MemoryItem, ReviewLog, User
from app.timeutil import user_day_bounds

settings = get_settings()
_STREAK_THRESHOLD = 5


def _now() -> datetime:
    return datetime.utcnow()


def _reviews_today(session: Session, user: User) -> int:
    start, end = user_day_bounds(user.timezone)
    stmt = select(func.count()).where(
        ReviewLog.user_id == user.id,
        ReviewLog.reviewed_at >= start,
        ReviewLog.reviewed_at < end,
    )
    value = session.exec(stmt).one()
    if isinstance(value, Sequence):
        value = value[0]
    return int(value or 0)


def schedule_from_mistake(
    session: Session,
    user: User,
    concept: str,
    task_id: Optional[UUID] = None,
) -> MemoryItem:
    stmt = select(MemoryItem).where(
        MemoryItem.user_id == user.id,
        MemoryItem.concept == concept,
    )
    memory = session.exec(stmt).first()
    due_at = _now() + timedelta(minutes=settings.SRS_LEEWAY_MIN)

    if memory is None:
        memory = MemoryItem(
            user_id=user.id,
            task_id=task_id,
            concept=concept,
            ease=2.5,
            interval=1,
            stability=0.0,
            difficulty=0.3,
            lapses=0,
            due_at=due_at,
        )
        session.add(memory)
    else:
        if task_id and memory.task_id is None:
            memory.task_id = task_id
        if memory.due_at > due_at:
            memory.due_at = due_at
    session.flush()
    return memory


def review(session: Session, user: User, memory: MemoryItem, grade: int) -> MemoryItem:
    grade = max(0, min(5, grade))
    now = _now()
    prev_interval = max(1, memory.interval)
    previous_due = memory.due_at

    ease_update = memory.ease + 0.1 - (5 - grade) * 0.08
    memory.ease = max(1.3, ease_update)

    if grade < 3:
        memory.interval = 1
        memory.lapses += 1
    else:
        bonus = max(0, grade - 3) * 0.15
        proposed = round(prev_interval * (memory.ease + bonus))
        memory.interval = max(1, proposed)

    memory.due_at = now + timedelta(days=memory.interval)
    memory.stability = max(memory.stability, float(memory.interval))
    memory.difficulty = max(0.0, min(1.0, memory.difficulty + (3 - grade) * 0.03))

    review_log = ReviewLog(
        user_id=user.id,
        memory_id=memory.id,
        grade=grade,
        scheduled_for=previous_due or now,
        reviewed_at=now,
        next_due_at=memory.due_at,
        delta_seconds=int((now - (previous_due or now)).total_seconds()),
    )
    session.add(review_log)
    session.flush()

    _update_streak(session, user)
    session.flush()
    return memory


def _update_streak(session: Session, user: User) -> None:
    today_count = _reviews_today(session, user)
    if today_count < _STREAK_THRESHOLD:
        return

    start, _ = user_day_bounds(user.timezone)
    last = user.last_streak_at
    if last is not None:
        last_start, _ = user_day_bounds(user.timezone, now=last)
        if last_start >= start:
            return
        if start - last_start == timedelta(days=1):
            user.streak_days += 1
        else:
            user.streak_days = 1
    else:
        user.streak_days = 1
    user.last_streak_at = start


def enforce_daily_cap(session: Session, user: User, requested: int) -> int:
    served = _reviews_today(session, user)
    remaining = max(0, settings.DAILY_REVIEW_CAP - served)
    return max(0, min(requested, remaining))


def get_next_reviews(session: Session, user: User, limit: int) -> List[MemoryItem]:
    if settings.KILL_SWITCH:
        return []
    limit = enforce_daily_cap(session, user, limit)
    if limit <= 0:
        return []
    now = _now()
    stmt = (
        select(MemoryItem)
        .where(
            MemoryItem.user_id == user.id,
            MemoryItem.due_at <= now,
        )
        .order_by(MemoryItem.due_at.asc())
        .limit(limit)
    )
    return list(session.exec(stmt).all())
