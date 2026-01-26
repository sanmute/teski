# routes/tasks.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlmodel import Session, select
from datetime import datetime, timedelta
from uuid import uuid4
import hashlib
import json
from pydantic import BaseModel
from models import Task
from schemas import TaskOut, TaskIn, MockLoadResp
from db import get_session
from services.scoring import score
from settings import DEFAULT_TIMEZONE
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

class TaskSimpleIn(BaseModel):
    title: str
    course: str | None = None
    kind: str | None = None
    due_at: datetime | None = None
    status: str | None = None
    base_estimated_minutes: int | None = None
    id: str | None = None
    source: str | None = None
    confidence: float | None = None
    notes: str | None = None


def _task_to_payload(task: Task, now: datetime | None = None) -> TaskOut:
    payload = task.model_dump(mode="json", exclude={"priority"})
    signals_raw = payload.pop("signals_json", None)
    payload["signals"] = json.loads(signals_raw) if signals_raw else None

    ts_now = now or datetime.now(DEFAULT_TIMEZONE)
    due_aware = task.due_iso if task.due_iso.tzinfo else task.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
    computed_priority, _ = score(ts_now, due_aware, task.status)
    payload["priority"] = computed_priority
    return TaskOut(**payload)

def _stable_int_id(task: Task) -> int:
    # Stable deterministic int ID for UI (needed because Task.id is a string/uuid)
    digest = hashlib.md5(task.id.encode("utf-8")).hexdigest()[:8]
    return int(digest, 16)

def _task_to_ui(task: Task) -> dict:
    return {
        "id": _stable_int_id(task),
        "title": task.title,
        "course": task.course,
        "kind": getattr(task, "task_type", None),
        "due_at": task.due_iso,
        "status": "done" if task.status == "done" else "pending",
        "personalized_estimated_minutes": task.estimated_minutes or 60,
        "blocks": [],
        "base_estimated_minutes": task.estimated_minutes or 60,
        "user_id": task.owner_user_id,
        "created_at": None,
        "updated_at": None,
    }

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

@router.get("/upcoming", response_model=list[dict])
def list_upcoming(session: Session = Depends(get_session)):
    now = datetime.now(DEFAULT_TIMEZONE)
    stmt = select(Task).where(Task.status != "done")
    tasks = session.exec(stmt).all()
    # Simple ordering: due date first, then created_at if available
    tasks.sort(key=lambda t: (t.due_iso or datetime.max))
    return [_task_to_ui(task) for task in tasks]

@router.post("", response_model=TaskOut)
def create_task(task: TaskIn | TaskSimpleIn = Body(...), session: Session = Depends(get_session)):
    if isinstance(task, TaskIn):
        t = Task(**task.model_dump())
    else:
        gen_id = task.id or str(uuid4())
        t = Task(
            id=gen_id,
            source=task.source or "mock",
            title=task.title,
            course=task.course,
            link=None,
            due_iso=task.due_at or datetime.now(DEFAULT_TIMEZONE) + timedelta(days=7),
            status=task.status if task.status in {"open", "done", "overdue"} else "open",
            confidence=task.confidence or 1.0,
            notes=task.notes,
            task_type=task.kind if hasattr(task, "kind") else None,
            estimated_minutes=getattr(task, "base_estimated_minutes", None) or getattr(task, "estimated_minutes", None),
            owner_user_id=None,
            suggested_start_utc=None,
            signals_json=None,
            completed_at=None,
        )
    session.add(t)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Task with this id already exists")
    session.refresh(t)
    return _task_to_payload(t)

@router.patch("/{ui_task_id}/status")
def update_status(
    ui_task_id: int = Path(..., ge=0),
    payload: dict = Body(...),
    session: Session = Depends(get_session),
):
    desired = payload.get("status")
    if desired not in {"pending", "done"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    tasks = session.exec(select(Task)).all()
    target = None
    for task in tasks:
        if _stable_int_id(task) == ui_task_id:
            target = task
            break
    if not target:
        raise HTTPException(status_code=404, detail="Task not found")
    target.status = "done" if desired == "done" else "open"
    target.completed_at = datetime.now(DEFAULT_TIMEZONE) if target.status == "done" else None
    session.add(target)
    session.commit()
    session.refresh(target)
    return _task_to_ui(target)
