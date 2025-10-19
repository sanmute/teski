from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session

from app.analytics import log as log_analytics
from app.config import get_settings
from app.db import get_session
from app.models import MemoryItem, XPEvent


@contextmanager
def _session_scope(session: Optional[Session] = None):
    if session is not None:
        yield session
        return
    session_gen = get_session()
    sess = next(session_gen)
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        try:
            session_gen.close()
        except RuntimeError:
            pass


def award(
    user: Any,
    reason: str,
    *,
    memory: Optional[MemoryItem] = None,
    base: Optional[int] = None,
    mastery_bonus: Optional[int] = None,
    session: Optional[Session] = None,
) -> int:
    settings = get_settings()
    base_amount = settings.XP_BASE if base is None else base
    bonus_amount = settings.XP_MASTERY_BONUS if mastery_bonus is None else mastery_bonus

    extra = 0
    if memory and memory.ease > 2.8 and memory.interval >= 21:
        extra = bonus_amount

    total = base_amount + extra
    if total <= 0:
        return 0

    user_id = getattr(user, "id", None) or str(user)
    if user_id is None:
        raise ValueError("XP award requires a user identifier")

    with _session_scope(session) as sess:
        event = XPEvent(
            id=None,
            user_id=user_id,
            amount=total,
            reason=reason,
            ts=datetime.utcnow(),
        )
        sess.add(event)

    log_analytics(
        "xp.awarded",
        {
            "reason": reason,
            "base": base_amount,
            "bonus": extra,
            "total": total,
        },
        user=user,
        session=session,
    )
    return total
