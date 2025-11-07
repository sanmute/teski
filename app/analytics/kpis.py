from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from ..db import get_session
from ..models import User
from .models import AnalyticsDailyAgg

router = APIRouter(prefix="/analytics/admin", tags=["analytics-admin"])


def _days_ago(days: int) -> date:
    return date.today() - timedelta(days=days)


def _user_set(rows: list[AnalyticsDailyAgg]) -> set[str]:
    return {str(row.user_id) for row in rows}


def _scalar(value: Any) -> float:
    if isinstance(value, tuple):
        return value[0]
    return value


@router.get("/kpis")
def kpis(session: Session = Depends(get_session)) -> Dict[str, Any]:
    today = date.today()
    d7 = _days_ago(7)
    d28 = _days_ago(28)

    rows_today = session.exec(select(AnalyticsDailyAgg).where(AnalyticsDailyAgg.day == today)).all()
    dau = len([row for row in rows_today if (row.sessions > 0 or row.reviews > 0)])

    rows7 = session.exec(select(AnalyticsDailyAgg).where(AnalyticsDailyAgg.day >= d7)).all()
    wau = len(_user_set(rows7))

    def _retention(window_days: int) -> float:
        start = _days_ago(window_days)
        prev_start = _days_ago(window_days * 2)
        recent_rows = session.exec(select(AnalyticsDailyAgg).where(AnalyticsDailyAgg.day >= start)).all()
        prev_rows = session.exec(
            select(AnalyticsDailyAgg).where(
                AnalyticsDailyAgg.day >= prev_start,
                AnalyticsDailyAgg.day < start,
            )
        ).all()
        prev_users = _user_set(prev_rows)
        if not prev_users:
            return 0.0
        kept = len(_user_set(recent_rows) & prev_users)
        return round(100.0 * kept / len(prev_users), 2)

    retention7 = _retention(7)
    retention28 = _retention(28)

    total_minutes = sum(row.minutes_active for row in rows7)
    total_sessions = sum(row.sessions for row in rows7)
    total_reviews = sum(row.reviews for row in rows7)
    users7 = max(wau, 1)

    avg_session_minutes = round(total_minutes / max(total_sessions, 1), 2)
    reviews_per_user = round(total_reviews / users7, 2)

    now_utc = datetime.utcnow()
    paid_row = session.exec(
        select(func.count(User.id)).where(
            (User.is_pro.is_(True))
            | (
                User.pro_until.is_not(None)
                & (User.pro_until > now_utc)
            )
        )
    ).one()
    paid_users = int(_scalar(paid_row) or 0)

    return {
        "dau": int(dau),
        "wau": int(wau),
        "retention7_pct": retention7,
        "retention28_pct": retention28,
        "avg_session_minutes": float(avg_session_minutes),
        "reviews_per_user_7d": float(reviews_per_user),
        "paid_users": paid_users,
        "window_7d_start": str(d7),
        "today": str(today),
    }
