from __future__ import annotations

from datetime import datetime, timedelta
from typing import Set

from sqlalchemy import delete
from sqlmodel import Session, select

from ..db import get_engine
from app.models import AnalyticsEvent
from .utils import rollup_events_to_daily

RETENTION_DAYS_RAW = 180
ROLLUP_LOOKBACK_DAYS = 2


def _distinct_user_ids_with_events(session: Session, since: datetime | None = None) -> Set[str]:
    query = select(AnalyticsEvent.user_id).distinct().where(AnalyticsEvent.user_id.is_not(None))
    if since:
        query = query.where(AnalyticsEvent.ts >= since)
    rows = session.exec(query).all()
    return {str(row) for row in rows if row}


def rollup_previous_day_for_all() -> dict:
    engine = get_engine()
    start = datetime.utcnow() - timedelta(days=ROLLUP_LOOKBACK_DAYS)
    with Session(engine) as session:
        user_ids = _distinct_user_ids_with_events(session, since=start - timedelta(days=1))
        rollups = 0
        for uid in user_ids:
            rollup_events_to_daily(session, uid)
            rollups += 1
    return {"users_considered": len(user_ids), "rollups_triggered": rollups}


def purge_old_raw_events() -> dict:
    engine = get_engine()
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS_RAW)
    with Session(engine) as session:
        stmt = delete(AnalyticsEvent).where(AnalyticsEvent.ts < cutoff)
        result = session.exec(stmt)
        deleted = result.rowcount or 0
        session.commit()
    return {"deleted_events": int(deleted), "cutoff_utc": cutoff.isoformat()}


def nightly_analytics_job() -> dict:
    rollup_result = rollup_previous_day_for_all()
    purge_result = purge_old_raw_events()
    return {"rollup": rollup_result, "purge": purge_result, "ran_at": datetime.utcnow().isoformat()}
