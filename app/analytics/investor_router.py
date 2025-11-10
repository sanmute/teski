from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from ..db import get_session
from ..deep.models import SelfExplanation
from ..feedback.costs import get_cost_stats
from ..pilot.models import PilotInvite, PilotSession

router = APIRouter(prefix="/analytics", tags=["analytics"])

_ALLOWED_WINDOWS = (30, 60, 90)


def _daterange(days: int) -> List[date]:
    today = date.today()
    return [today - timedelta(days=offset) for offset in range(days)][::-1]


def _normalize_day(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _safe_all(session: Session, stmt) -> list:
    try:
        return session.exec(stmt).all()
    except SQLAlchemyError:
        return []


def _series_bounds(days: List[date]) -> tuple[datetime, datetime]:
    if not days:
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)
        return start, end
    start = datetime.combine(days[0], datetime.min.time())
    end = datetime.combine(days[-1] + timedelta(days=1), datetime.min.time())
    return start, end


def _session_daily_stats(session: Session, start: datetime, end: datetime) -> Dict[str, Dict[str, float]]:
    day_expr = func.date(PilotSession.started_at)
    stmt = (
        select(
            day_expr.label("day"),
            func.count(func.distinct(PilotSession.user_id)).label("dau"),
            func.coalesce(func.sum(PilotSession.minutes_active), 0).label("minutes"),
        )
        .where(PilotSession.started_at >= start, PilotSession.started_at < end)
        .group_by(day_expr)
    )
    rows = _safe_all(session, stmt)
    data: Dict[str, Dict[str, float]] = {}
    for day_value, dau_value, minutes_value in rows:
        key = _normalize_day(day_value)
        data[key] = {
            "dau": int(dau_value or 0),
            "minutes": float(minutes_value or 0.0),
        }
    return data


def _week_start(dt: datetime | date) -> date:
    if isinstance(dt, datetime):
        dt = dt.date()
    return dt - timedelta(days=dt.weekday())


@router.get("/investor")
def investor(range_days: int = 30, session: Session = Depends(get_session)) -> Dict[str, Any]:
    if range_days not in _ALLOWED_WINDOWS:
        range_days = 30

    days = _daterange(range_days)
    window_start, window_end = _series_bounds(days)

    session_stats = _session_daily_stats(session, window_start, window_end)

    dau_series = [
        {"date": d.isoformat(), "dau": int(session_stats.get(d.isoformat(), {}).get("dau", 0))}
        for d in days
    ]
    minutes_series = [
        {
            "date": d.isoformat(),
            "minutes": int(round(session_stats.get(d.isoformat(), {}).get("minutes", 0))),
        }
        for d in days
    ]

    depth_day_expr = func.date(SelfExplanation.created_at)
    depth_stmt = (
        select(
            depth_day_expr.label("day"),
            func.avg(SelfExplanation.score_deep).label("avg_depth"),
        )
        .where(SelfExplanation.created_at >= window_start, SelfExplanation.created_at < window_end)
        .group_by(depth_day_expr)
    )
    depth_rows = _safe_all(session, depth_stmt)
    depth_map = {
        _normalize_day(day_value): float(avg_value or 0.0)
        for day_value, avg_value in depth_rows
    }
    depth_series = [
        {"date": d.isoformat(), "avg_depth": round(depth_map.get(d.isoformat(), 0.0), 2)}
        for d in days
    ]

    score_stmt = select(SelfExplanation.score_deep).where(
        SelfExplanation.created_at >= window_start,
        SelfExplanation.created_at < window_end,
    )
    score_rows = _safe_all(session, score_stmt)
    bins = [0] * 10
    for (score_value,) in score_rows:
        score = float(score_value or 0.0)
        idx = min(9, max(0, int(score // 10)))
        bins[idx] += 1
    depth_hist = [
        {"bucket": f"{10 * idx}-{10 * idx + 9}", "count": count}
        for idx, count in enumerate(bins)
    ]

    cohorts: List[Dict[str, Any]] = []
    invite_stmt = select(PilotInvite.used_by_user, PilotInvite.used_at).where(
        PilotInvite.used_by_user.is_not(None),
        PilotInvite.used_at.is_not(None),
    )
    invite_rows = _safe_all(session, invite_stmt)
    if invite_rows:
        cohort_map: Dict[date, set[str]] = {}
        for user_id, used_at in invite_rows:
            if not used_at:
                continue
            ws = _week_start(used_at)
            cohort_map.setdefault(ws, set()).add(str(user_id))

        activity_stmt = select(PilotSession.user_id, PilotSession.started_at)
        activity_rows = _safe_all(session, activity_stmt)
        activity_by_week: Dict[date, set[str]] = {}
        for user_id, started_at in activity_rows:
            if not started_at:
                continue
            wk = _week_start(started_at)
            activity_by_week.setdefault(wk, set()).add(str(user_id))

        for cohort_week in sorted(cohort_map.keys()):
            members = cohort_map[cohort_week]
            size = len(members) or 1
            row = {"cohort": cohort_week.isoformat()}
            for offset in range(5):
                target_week = cohort_week + timedelta(days=7 * offset)
                active = activity_by_week.get(target_week, set())
                retain_pct = round((len(members & active) / size) * 100, 1)
                row[f"W{offset}"] = retain_pct
            cohorts.append(row)

    costs = get_cost_stats(session)
    last_30_days = _daterange(30)
    last_30_start, last_30_end = _series_bounds(last_30_days)
    last_30_stats = _session_daily_stats(session, last_30_start, last_30_end)
    dau_30_total = sum(day_stat.get("dau", 0) for day_stat in last_30_stats.values())
    cost_per_active = costs.get("cost_last_30d_eur", 0.0) / max(1, dau_30_total)

    return {
        "range_days": range_days,
        "dau": dau_series,
        "avg_depth": depth_series,
        "minutes": minutes_series,
        "cohorts": cohorts,
        "depth_hist": depth_hist,
        "costs": {
            "total_eur": float(costs.get("cost_total_eur", 0.0)),
            "last_30d_eur": float(costs.get("cost_last_30d_eur", 0.0)),
            "events_total": int(costs.get("events_total", 0)),
            "cache_hit_rate": float(costs.get("cache_hit_rate", 0.0)),
            "cost_per_active_user_30d": round(float(cost_per_active), 4),
        },
    }
