from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.db import get_session
from app.models import AnalyticsEvent

logger = logging.getLogger("teski.analytics")


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


def log_event(kind: str, payload: Dict[str, Any] | None = None, user_id: Optional[str] = None, *, session: Optional[Session] = None) -> None:
    payload = payload or {}
    with _session_scope(session) as sess:
        event = AnalyticsEvent(
            id=None,
            user_id=user_id,
            kind=kind,
            payload=payload,
            ts=datetime.utcnow(),
        )
        sess.add(event)
    logger.debug("analytics event %s recorded for user %s", kind, user_id)


# backwards compatible alias requested in prompt
def log(kind: str, payload: Dict[str, Any] | None = None, user: Optional[Any] = None, *, session: Optional[Session] = None) -> None:
    user_id = None
    if user is not None:
        user_id = getattr(user, "id", None) or str(user)
    log_event(kind, payload, user_id, session=session)
