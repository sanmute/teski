# app/backend/routes/reminders.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from db import get_session
from models import Task, Reminder
from schemas import NextReminderReq, NextReminderOut
from services.scoring import score, script_hint
from services.reminder_engine import run_sweep, maybe_create_reminder_for_task  # <-- add this module
from settings import DEFAULT_TIMEZONE

router = APIRouter(prefix="/reminders", tags=["reminders"])


# ---------------------------
# Existing: pick the next reminder target deterministically
# ---------------------------
@router.post("/next", response_model=NextReminderOut)
def next_reminder(req: NextReminderReq, session: Session = Depends(get_session)):
    # Pick the most urgent OPEN/OVERDUE task
    now = datetime.now(DEFAULT_TIMEZONE)
    tasks = session.exec(select(Task).where(Task.status != "done")).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="No pending tasks")

    # Score all and choose highest priority, then earliest due
    scored: list[tuple[int, datetime, str, Task]] = []
    for t in tasks:
        # Ensure aware datetimes (store UTC in DB; coerce if naive)
        due_aware = t.due_iso if t.due_iso.tzinfo else t.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
        if due_aware.tzinfo is not DEFAULT_TIMEZONE:
            due_aware = due_aware.astimezone(DEFAULT_TIMEZONE)
        prio, esc = score(now, due_aware, t.status)
        scored.append((prio, due_aware, esc, t))

    scored.sort(key=lambda x: (-x[0], x[1]))  # high prio first, then earliest due
    prio, due_aware, esc, t = scored[0]

    hours = (due_aware - now).total_seconds() / 3600.0
    hints = script_hint(t.title, esc, hours)

    return NextReminderOut(
        taskId=t.id,
        escalation=esc,
        persona=req.persona,
        scriptHints=hints,
        due_iso=due_aware,
        title=t.title,
        priority=prio,
    )


# ---------------------------
# New: run a sweep to create reminders for due tasks (cooldown-aware)
# ---------------------------
@router.post("/run")
def run_reminder_sweep(
    persona: str = Query("teacher", description="persona key used for created reminders"),
    session: Session = Depends(get_session),
):
    checked, created = run_sweep(session, persona=persona)
    return {"checked": checked, "created": created}


# ---------------------------
# New: create a reminder for a single task (respects cooldowns)
# ---------------------------
@router.post("/create")
def create_for_task(
    taskId: str,
    persona: str = Query("teacher"),
    session: Session = Depends(get_session),
):
    task = session.get(Task, taskId)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    rem = maybe_create_reminder_for_task(session, task, persona=persona)
    if not rem:
        return {"created": False, "reason": "cooldown or low priority"}
    return {"created": True, "reminder_id": rem.id}


# ---------------------------
# New: read reminder history (global or per task)
# ---------------------------
@router.get("/history")
def reminder_history(
    taskId: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    q = select(Reminder).order_by(Reminder.created_at.desc()).limit(limit)
    if taskId:
        q = (
            select(Reminder)
            .where(Reminder.task_id == taskId)
            .order_by(Reminder.created_at.desc())
            .limit(limit)
        )
    rows = session.exec(q).all()
    return [
        {
            "id": r.id,
            "taskId": r.task_id,
            "escalation": r.escalation,
            "persona": r.persona,
            "created_at": r.created_at,
            # Reuse script_hints to carry the displayable message (no schema change needed)
            "message": r.script_hints,
        }
        for r in rows
    ]
