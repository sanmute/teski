from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, Any
from uuid import UUID

from sqlmodel import Session, select

from app.models import AnalyticsEvent
from .models import AnalyticsDailyAgg

ROLLUP_WINDOW_DAYS_DEFAULT = 7
SESSION_EVENT_KINDS = {"memory.review_fetch", "memory.review_shown"}
REVIEW_EVENT_KINDS = {"memory.review_logged", "exercise_correct", "exercise_incorrect"}
MINUTE_PAYLOAD_CANDIDATES = ("minutes", "minutes_active", "duration_minutes")


def _ensure_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError:
        return None


def _extract_minutes(event: AnalyticsEvent) -> float:
    payload = event.payload or {}
    for key in MINUTE_PAYLOAD_CANDIDATES:
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


def rollup_events_to_daily(session: Session, user_id: str | UUID, *, window_days: int = ROLLUP_WINDOW_DAYS_DEFAULT) -> None:
    """
    Recompute per-day counts for the specified user across the recent window.
    """
    user_uuid = _ensure_uuid(user_id)
    if user_uuid is None:
        return

    now = datetime.utcnow()
    start = now - timedelta(days=window_days)
    rows = session.exec(
        select(AnalyticsEvent).where(
            AnalyticsEvent.user_id == user_uuid,
            AnalyticsEvent.ts >= start - timedelta(days=1),
        )
    ).all()

    buckets: dict[date, Dict[str, Any]] = {}
    for ev in rows:
        day = ev.ts.date()
        bucket = buckets.setdefault(
            day,
            {
                "counts": defaultdict(int),
                "sessions": 0,
                "reviews": 0,
                "minutes": 0.0,
            },
        )
        bucket["counts"][ev.kind] += 1
        if ev.kind in SESSION_EVENT_KINDS:
            bucket["sessions"] += 1
        if ev.kind in REVIEW_EVENT_KINDS:
            bucket["reviews"] += 1
        bucket["minutes"] += _extract_minutes(ev)

    for bucket_day, payload in buckets.items():
        agg = session.exec(
            select(AnalyticsDailyAgg).where(
                AnalyticsDailyAgg.user_id == user_uuid,
                AnalyticsDailyAgg.day == bucket_day,
            )
        ).first()
        counts = {k: int(v) for k, v in payload["counts"].items()}
        if agg:
            agg.counts = counts
            agg.sessions = int(payload["sessions"])
            agg.reviews = int(payload["reviews"])
            agg.minutes_active = float(payload["minutes"])
            agg.last_recomputed_at = now
        else:
            agg = AnalyticsDailyAgg(
                user_id=user_uuid,
                day=bucket_day,
                counts=counts,
                sessions=int(payload["sessions"]),
                reviews=int(payload["reviews"]),
                minutes_active=float(payload["minutes"]),
                last_recomputed_at=now,
            )
            session.add(agg)

    session.commit()
