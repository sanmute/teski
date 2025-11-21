from __future__ import annotations

"""Backfill legacy Teski data into the new app schema.

Run with TESKI_MEMORY_V2_DUAL_WRITE disabled and ensure backups are taken first.
"""

import json
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlmodel import Session, select

from backend.db import engine as legacy_engine
from backend.models import Task as LegacyTask
from backend.models import User as LegacyUser
from backend.models_memory import MistakeLog
from backend.models_leaderboard import PointsEvent

from app.db import get_session as get_app_session
from app.models import (
    LegacyTaskMap,
    LegacyUserMap,
    MemoryItem,
    Mistake,
    Task as NewTask,
    User as NewUser,
    XPEvent,
)


def _concept_from_mistake(row: dict) -> str:
    template_code = row.get("template_code")
    if template_code:
        return template_code
    skill_id = row.get("skill_id")
    if skill_id is not None:
        return f"skill:{skill_id}"
    return "unknown"


def _coerce_datetime(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.utcnow()
    if getattr(value, "tzinfo", None):
        return value.replace(tzinfo=None)
    return value


def _ensure_user(app_session: Session, legacy_user: LegacyUser) -> NewUser:
    mapping = app_session.get(LegacyUserMap, legacy_user.id)
    if mapping:
        user = app_session.get(NewUser, mapping.user_id)
        if user:
            return user
    user = NewUser(
        id=uuid4(),
        created_at=_coerce_datetime(getattr(legacy_user, "created_at", None)),
        timezone="UTC",
        display_name=legacy_user.display_name,
        persona=None,
    )
    app_session.add(user)
    app_session.add(LegacyUserMap(legacy_user_id=legacy_user.id, user_id=user.id))
    app_session.flush()
    return user


def _ensure_task(app_session: Session, legacy_task: LegacyTask, user_id) -> Optional[NewTask]:
    if not legacy_task:
        return None
    mapping = app_session.get(LegacyTaskMap, legacy_task.id)
    if mapping:
        return app_session.get(NewTask, mapping.task_id)
    task = NewTask(
        id=uuid4(),
        user_id=user_id,
        title=legacy_task.title,
        course=legacy_task.course,
        due_at=_coerce_datetime(legacy_task.due_iso),
        created_at=_coerce_datetime(getattr(legacy_task, "created_at", None) or legacy_task.due_iso),
    )
    app_session.add(task)
    app_session.add(LegacyTaskMap(legacy_task_id=legacy_task.id, task_id=task.id))
    app_session.flush()
    return task


def migrate_users(app_session: Session, legacy_session: Session) -> Dict[int, NewUser]:
    mapping: Dict[int, NewUser] = {}
    for legacy_user in legacy_session.exec(select(LegacyUser)).all():
        mapping[legacy_user.id] = _ensure_user(app_session, legacy_user)
    return mapping


def migrate_tasks(app_session: Session, legacy_session: Session, user_map: Dict[int, NewUser]) -> None:
    for legacy_task in legacy_session.exec(select(LegacyTask)).all():
        owner_id = None
        if legacy_task.owner_user_id and legacy_task.owner_user_id.isdigit():
            owner_id = int(legacy_task.owner_user_id)
        if owner_id and owner_id in user_map:
            _ensure_task(app_session, legacy_task, user_map[owner_id].id)


def migrate_mistakes(app_session: Session, legacy_session: Session, user_map: Dict[int, NewUser]) -> None:
    inspector = inspect(legacy_session.bind)
    columns = {col["name"] for col in inspector.get_columns(MistakeLog.__tablename__)}
    has_subtype = "error_subtype" in columns
    column_list = [
        "id",
        "user_id",
        "skill_id",
        "template_code",
        "instance_id",
        "error_type",
        "detail",
        "weight",
        "occurred_at",
        "resolved_at",
    ]
    if has_subtype:
        column_list.append("error_subtype")
    sql = text(
        "SELECT " + ",".join(column_list) + f" FROM {MistakeLog.__tablename__}"
    )
    rows = legacy_session.execute(sql).mappings().all()
    for row in rows:
        legacy_user_id = row["user_id"]
        if legacy_user_id not in user_map:
            continue
        concept = _concept_from_mistake(row)
        user = user_map[legacy_user_id]
        task = None
        template_code = row.get("template_code")
        if template_code:
            legacy_task = legacy_session.get(LegacyTask, template_code)
            task = _ensure_task(app_session, legacy_task, user.id) if legacy_task else None
        memory = app_session.exec(
            select(MemoryItem).where(MemoryItem.user_id == user.id, MemoryItem.concept == concept)
        ).first()
        if memory is None:
            memory = MemoryItem(
                id=uuid4(),
                user_id=user.id,
                task_id=getattr(task, "id", None),
                concept=concept,
                ease=2.5,
                interval=1,
                due_at=_coerce_datetime(row.get("occurred_at")),
                stability=0.0,
                difficulty=0.3,
                lapses=0,
            )
            app_session.add(memory)
        subtype_value = row.get("error_subtype") if has_subtype else None
        subtype = subtype_value or row.get("error_type") or "other"
        label = subtype if ":" in subtype else f"legacy:{subtype}"
        detail = row.get("detail") or {}
        if not isinstance(detail, dict):
            try:
                detail = json.loads(detail)
            except (TypeError, json.JSONDecodeError):
                detail = {"raw": str(detail)}
        mistake = Mistake(
            id=uuid4(),
            user_id=user.id,
            task_id=getattr(task, "id", None),
            concept=concept,
            subtype=label,
            raw=json.dumps(detail, default=str),
            created_at=_coerce_datetime(row.get("occurred_at")),
        )
        app_session.add(mistake)


def migrate_xp(app_session: Session, legacy_session: Session, user_map: Dict[int, NewUser]) -> None:
    for event in legacy_session.exec(select(PointsEvent)).all():
        if event.user_id not in user_map:
            continue
        app_session.add(
            XPEvent(
                id=uuid4(),
                user_id=user_map[event.user_id].id,
                amount=event.points,
                reason=event.event_type,
                ts=_coerce_datetime(event.occurred_at),
            )
        )


def main() -> None:
    legacy_session = Session(legacy_engine)
    app_session_gen = get_app_session()
    app_session = next(app_session_gen)
    try:
        user_map = migrate_users(app_session, legacy_session)
        migrate_tasks(app_session, legacy_session, user_map)
        migrate_mistakes(app_session, legacy_session, user_map)
        migrate_xp(app_session, legacy_session, user_map)
        app_session.commit()
    finally:
        app_session.close()
        legacy_session.close()
        try:
            app_session_gen.close()
        except RuntimeError:
            pass


if __name__ == "__main__":
    main()
