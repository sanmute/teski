# routes/tasks.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta
import json
from ..models import Task
from ..schemas import TaskOut, TaskIn, MockLoadResp
from ..db import get_session
from ..services.scoring import score
from ..settings import DEFAULT_TIMEZONE
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _task_to_payload(task: Task, now: datetime | None = None) -> TaskOut:
    payload = task.model_dump(mode="json", exclude={"priority"})
    signals_raw = payload.pop("signals_json", None)
    payload["signals"] = json.loads(signals_raw) if signals_raw else None

    ts_now = now or datetime.now(DEFAULT_TIMEZONE)
    due_aware = task.due_iso if task.due_iso.tzinfo else task.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
    computed_priority, _ = score(ts_now, due_aware, task.status)
    payload["priority"] = computed_priority
    return TaskOut(**payload)

@router.get("", response_model=list[TaskOut])
def list_tasks(session: Session = Depends(get_session), include_overdue: bool = True):
    now = datetime.now(DEFAULT_TIMEZONE)
    purge_before = now - timedelta(hours=36)
    tasks = session.exec(select(Task)).all()
    has_real_tasks = any(t.source != "mock" for t in tasks)
    visible: list[TaskOut] = []
    for task in tasks:
        if has_real_tasks and task.source == "mock":
            continue
        due = task.due_iso if task.due_iso.tzinfo else task.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
        if task.status == "overdue" and due < purge_before:
            session.delete(task)
            continue
        if not include_overdue and task.status == "overdue":
            continue
        visible.append(_task_to_payload(task, now=now))

    def sort_key(item: TaskOut):
        if item.status == "overdue":
            status_rank = 0
        elif item.status == "done":
            status_rank = 2
        else:
            status_rank = 1
        return (status_rank, item.priority * -1, item.due_iso)

    visible.sort(key=sort_key)
    session.commit()
    return visible

@router.post("", response_model=TaskOut)
def create_task(task: TaskIn, session: Session = Depends(get_session)):
    t = Task(**task.model_dump())
    session.add(t)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Task with this id already exists")
    session.refresh(t)
    return _task_to_payload(t)
