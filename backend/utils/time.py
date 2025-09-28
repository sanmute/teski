# >>> LEADERBOARD START TIME UTILS
"""Time helper utilities for leaderboard scoring."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple

from zoneinfo import ZoneInfo

from backend.core.leaderboard_constants import DEFAULT_TZ


def now_utc() -> datetime:
    """Return the current UTC-aware datetime."""

    return datetime.now(tz=ZoneInfo("UTC"))


def to_week_key(dt: datetime) -> Tuple[int, int]:
    """Return ISO (year, week number) for the provided datetime."""

    iso_year, iso_week, _ = dt.isocalendar()
    return int(iso_year), int(iso_week)


def start_end_of_week_iso(year: int, week: int, tz_str: str = DEFAULT_TZ) -> Tuple[datetime, datetime]:
    """Return the UTC-aware start and end datetimes for an ISO week in a timezone."""

    tz = ZoneInfo(tz_str)
    # ISO weeks start on Monday
    first_day = datetime.fromisocalendar(year, week, 1)
    start = datetime.combine(first_day.date(), datetime.min.time(), tzinfo=tz)
    end = start + timedelta(days=7)
    return start, end
# >>> LEADERBOARD END TIME UTILS
