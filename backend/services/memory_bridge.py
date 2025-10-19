from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlmodel import Session, select

from backend.models import Task as LegacyTask
from backend.models import User as LegacyUser
from backend.settings import memory_settings
from app.db import get_session as get_app_session
from app.models import (
    LegacyTaskMap,
    LegacyUserMap,
    MemoryItem,
    Mistake,
    MistakeSubtype,
    Task as NewTask,
    User as NewUser,
    XPEvent,
)
from app.scheduler import review as scheduler_review, schedule_from_mistake


def _should_dual_write() -> bool:
    return getattr(memory_settings, "MEMORY_V2_DUAL_WRITE", False)


@contextmanager
def _session_scope() -> Session:
    gen = get_app_session()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            gen.close()
        except RuntimeError:
            pass


def _coerce_datetime(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.utcnow()
    if getattr(value, "tzinfo", None) is not None:
        return value.replace(tzinfo=None)
    return value


def record_mistake_dual_write(
    legacy_session,
    *,
    user_id: int,
    concept: Optional[str],
    subtype: str,
    detail: Any,
    task_id: Optional[str] = None,
) -> None:
    if not _should_dual_write():
        return

    legacy_user = legacy_session.get(LegacyUser, user_id)
    if not legacy_user:
        return

    legacy_task = legacy_session.get(LegacyTask, task_id) if task_id else None

    payload = detail
    if not isinstance(payload, str):
        try:
            payload = json.dumps(payload, default=str)
        except TypeError:
            payload = str(payload)

    with _session_scope() as session:
        try:
            new_user_id = _ensure_user(session, legacy_user)
            new_task_id = None
            if legacy_task:
                new_task_id = _ensure_task(session, new_user_id, legacy_task)
            _upsert_memory_and_mistake(
                session,
                user_id=new_user_id,
                concept=(concept or "unknown"),
                subtype=subtype,
                raw=payload,
                new_task_id=new_task_id,
            )
            session.commit()
        except Exception:
            session.rollback()
            raise


def _ensure_user(session: Session, legacy_user: LegacyUser) -> UUID:
    mapping = session.get(LegacyUserMap, legacy_user.id)
    if mapping:
        return mapping.user_id

    new_user = NewUser(
        id=uuid4(),
        created_at=_coerce_datetime(getattr(legacy_user, "created_at", None)),
        timezone="UTC",
        display_name=legacy_user.display_name,
        persona=None,
    )
    session.add(new_user)
    session.add(
        LegacyUserMap(
            legacy_user_id=legacy_user.id,
            user_id=new_user.id,
        )
    )
    session.flush()
    return new_user.id


def _ensure_task(session: Session, new_user_id: UUID, legacy_task: LegacyTask) -> UUID:
    mapping = session.get(LegacyTaskMap, legacy_task.id)
    if mapping:
        return mapping.task_id

    new_task = NewTask(
        id=uuid4(),
        user_id=new_user_id,
        title=legacy_task.title,
        course=legacy_task.course,
        due_at=_coerce_datetime(getattr(legacy_task, "due_iso", None)),
        created_at=_coerce_datetime(getattr(legacy_task, "created_at", None)),
    )
    session.add(new_task)
    session.add(
        LegacyTaskMap(
            legacy_task_id=legacy_task.id,
            task_id=new_task.id,
        )
    )
    session.flush()
    return new_task.id


def _upsert_memory_and_mistake(
    session: Session,
    *,
    user_id: UUID,
    concept: str,
    subtype: str,
    raw: str,
    new_task_id: Optional[UUID],
) -> None:
    try:
        subtype_enum = MistakeSubtype(subtype)
    except ValueError:
        subtype_enum = MistakeSubtype.OTHER

    result = session.exec(
        select(MemoryItem).where(
            MemoryItem.user_id == user_id,
            MemoryItem.concept == concept,
        )
    )
    memory = result.first()
    if memory is None:
        memory = MemoryItem(
            id=uuid4(),
            user_id=user_id,
            task_id=new_task_id,
            concept=concept,
            due_at=datetime.utcnow(),
            ease=2.5,
            interval=1,
            stability=0.0,
            difficulty=0.3,
            lapses=0,
        )
        session.add(memory)

    session.add(
        Mistake(
            id=uuid4(),
            user_id=user_id,
            task_id=new_task_id,
            concept=concept,
            subtype=subtype_enum,
            raw=raw,
        )
    )


def record_review_dual_write(
    legacy_session,
    *,
    user_id: int,
    concept: Optional[str],
    grade: int,
    task_id: Optional[str] = None,
) -> None:
    if not _should_dual_write():
        return

    legacy_user = legacy_session.get(LegacyUser, user_id)
    if not legacy_user:
        return

    legacy_task = legacy_session.get(LegacyTask, task_id) if task_id else None

    with _session_scope() as session:
        try:
            new_user_id = _ensure_user(session, legacy_user)
            new_task_id = None
            if legacy_task:
                new_task_id = _ensure_task(session, new_user_id, legacy_task)

            concept_value = concept or (legacy_task.title if legacy_task else "unknown")

            memory = session.exec(
                select(MemoryItem).where(
                    MemoryItem.user_id == new_user_id,
                    MemoryItem.concept == concept_value,
                )
            ).first()
            new_user = session.get(NewUser, new_user_id)
            if memory is None:
                memory = schedule_from_mistake(
                    session,
                    user=new_user,
                    concept=concept_value,
                    task_id=new_task_id,
                )
            scheduler_review(session, new_user, memory, grade)
            session.commit()
        except Exception:
            session.rollback()
            raise


def record_xp_event(
    legacy_session,
    *,
    user_id: int,
    amount: int,
    reason: str,
) -> None:
    if not _should_dual_write():
        return

    legacy_user = legacy_session.get(LegacyUser, user_id)
    if not legacy_user:
        return

    with _session_scope() as session:
        try:
            new_user_id = _ensure_user(session, legacy_user)
            session.add(
                XPEvent(
                    id=uuid4(),
                    user_id=new_user_id,
                    amount=amount,
                    reason=reason,
                    ts=datetime.utcnow(),
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
