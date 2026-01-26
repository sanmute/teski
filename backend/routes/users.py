from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
import json
from db import get_session
from models import Task, Reminder
from models_studypack import StudyPack
from models_integrations import MoodleFeed
from services.scoring import score

router = APIRouter(prefix="/api/users", tags=["users"])

@router.delete("/{user_id}/purge")
def purge_user_data(user_id: str, session: Session = Depends(get_session)):
    # find task ids owned by this user
    task_rows = session.exec(select(Task.id).where(Task.owner_user_id == user_id)).all()
    task_ids = [tid for (tid,) in task_rows] if task_rows and isinstance(task_rows[0], tuple) else list(task_rows)

    # delete reminders for those tasks
    rem_del = session.exec(delete(Reminder).where(Reminder.task_id.in_(task_ids))).rowcount if task_ids else 0
    # delete study packs for those tasks
    sp_del = session.exec(delete(StudyPack).where(StudyPack.task_id.in_(task_ids))).rowcount if task_ids else 0
    # delete tasks
    t_del = session.exec(delete(Task).where(Task.owner_user_id == user_id)).rowcount

    # delete the moodle feed row
    mf_del = session.exec(delete(MoodleFeed).where(MoodleFeed.user_id == user_id)).rowcount

    session.commit()
    return {
        "deleted": {
            "moodleFeed": mf_del,
            "tasks": t_del,
            "reminders": rem_del,
            "studyPacks": sp_del
        }
    }
from datetime import datetime
from schemas import TaskOut
from settings import DEFAULT_TIMEZONE

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

def _now_local():
    return datetime.now(DEFAULT_TIMEZONE)

@router.post("/{task_id}/done", response_model=TaskOut)
def mark_done(task_id: str, session: Session = Depends(get_session)):
    t = session.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.status = "done"
    t.completed_at = _now_local().isoformat()
    session.add(t); session.commit(); session.refresh(t)
    payload = t.model_dump(mode="json", exclude={"priority"})
    signals_raw = payload.pop("signals_json", None)
    payload["signals"] = json.loads(signals_raw) if signals_raw else None
    return TaskOut(**{**payload, "priority": 0})

@router.post("/{task_id}/undo", response_model=TaskOut)
def undo_done(task_id: str, session: Session = Depends(get_session)):
    t = session.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.status = "open"
    t.completed_at = None
    session.add(t); session.commit(); session.refresh(t)
    now = _now_local()
    due_aware = t.due_iso if t.due_iso.tzinfo else t.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
    computed_priority, _ = score(now, due_aware, t.status)
    payload = t.model_dump(mode="json", exclude={"priority"})
    signals_raw = payload.pop("signals_json", None)
    payload["signals"] = json.loads(signals_raw) if signals_raw else None
    payload["priority"] = computed_priority
    return TaskOut(**payload)

# Optional: generic status setter (if you want one)
@router.patch("/{task_id}/status", response_model=TaskOut)
def set_status(task_id: str, status: str, session: Session = Depends(get_session)):
    if status not in {"open","done","overdue"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    t = session.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    t.status = status
    t.completed_at = _now_local().isoformat() if status == "done" else None
    session.add(t); session.commit(); session.refresh(t)
    payload = t.model_dump(mode="json", exclude={"priority"})
    signals_raw = payload.pop("signals_json", None)
    payload["signals"] = json.loads(signals_raw) if signals_raw else None
    priority_value = 0 if status == "done" else score(_now_local(), t.due_iso if t.due_iso.tzinfo else t.due_iso.replace(tzinfo=DEFAULT_TIMEZONE), t.status)[0]
    payload["priority"] = priority_value
    return TaskOut(**payload)
