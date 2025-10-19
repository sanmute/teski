from __future__ import annotations

from datetime import datetime
from typing import Optional

from contextlib import contextmanager

from sqlmodel import Session, select

from app.analytics import log as log_analytics
from app.db import get_session
from app.models import Badge, MemoryItem, ReviewLog


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


def check_nemesis(user, concept: str, *, session: Optional[Session] = None) -> bool:
    with _session_scope(session) as sess:
        user_id = getattr(user, "id", user)
        memory = sess.exec(
            select(MemoryItem).where(
                MemoryItem.user_id == user_id,
                MemoryItem.concept == concept,
            )
        ).first()
        if memory is None or memory.lapses < 2:
            return False

        reviews = sess.exec(
            select(ReviewLog)
            .where(ReviewLog.memory_id == memory.id)
            .order_by(ReviewLog.reviewed_at.desc())
            .limit(3)
        ).all()
        if len(reviews) < 3:
            return False
        if not all(r.grade >= 4 for r in reviews):
            return False

        badge_kind = f"Nemesis::{concept}"
        existing = sess.exec(select(Badge).where(Badge.user_id == user_id, Badge.kind == badge_kind)).first()
        if existing:
            return True

        badge = Badge(
            id=None,
            user_id=user_id,
            kind=badge_kind,
            acquired_at=datetime.utcnow(),
        )
        sess.add(badge)

    log_analytics(
        "badge.earned",
        {"kind": "Nemesis", "concept": concept},
        user=user,
        session=sess,
    )
    return True
