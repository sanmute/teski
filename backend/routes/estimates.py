from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from datetime import datetime, timedelta
import json
from db import get_session
from models import Task
from services.effort import analyze_assignment as analyze
from settings import DEFAULT_TIMEZONE

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("/{task_id}/estimate")
def estimate_task(task_id: str, session: Session = Depends(get_session)):
    t = session.get(Task, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    due = t.due_iso if t.due_iso.tzinfo else t.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
    desc = t.notes or ""
    eff = analyze(t.title, desc, due, getattr(t, "link", None))
    # persist
    t.task_type = eff["task_type"]
    t.estimated_minutes = eff["estimated_minutes"]
    start_val = eff.get("suggested_start_utc")
    if isinstance(start_val, str):
        suggested_dt = datetime.fromisoformat(start_val.replace("Z", "+00:00"))
    else:
        suggested_dt = start_val
    if suggested_dt.tzinfo is None:
        suggested_dt = suggested_dt.replace(tzinfo=DEFAULT_TIMEZONE)
    else:
        suggested_dt = suggested_dt.astimezone(DEFAULT_TIMEZONE)
    t.suggested_start_utc = suggested_dt
    t.signals_json = json.dumps(eff.get("signals") or {})
    session.add(t); session.commit(); session.refresh(t)

    # also compute "finish if you start now" time for the UI
    now = datetime.now(DEFAULT_TIMEZONE)
    finish_now = (now + timedelta(minutes=eff["estimated_minutes"]))

    return {
        "taskId": t.id,
        "task_type": t.task_type,
        "estimated_minutes": t.estimated_minutes,
        "suggested_start_utc": t.suggested_start_utc,
        "finish_if_start_now_utc": finish_now.isoformat(),
        "signals": eff["signals"],
    }
