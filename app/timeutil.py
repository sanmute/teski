from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple
from zoneinfo import ZoneInfo

DEFAULT_TZ = "Europe/Helsinki"


def _ensure_utc(dt: datetime | None = None) -> datetime:
    """Return an aware UTC datetime for calculations."""
    dt = dt or datetime.utcnow()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _resolve_tz(tz_str: str | None) -> ZoneInfo:
    tz_name = (tz_str or DEFAULT_TZ).strip() or DEFAULT_TZ
    try:
        return ZoneInfo(tz_name)
    except Exception:  # pragma: no cover - fallback for invalid tz names
        return ZoneInfo(DEFAULT_TZ)


def user_day_bounds(tz_str: str | None = None, *, now: datetime | None = None) -> Tuple[datetime, datetime]:
    """Return the UTC bounds (inclusive start, exclusive end) for the user's current local day."""
    tz = _resolve_tz(tz_str)
    current_utc = _ensure_utc(now)
    local_now = current_utc.astimezone(tz)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    local_end = local_start + timedelta(days=1)

    start_utc = local_start.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = local_end.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc
