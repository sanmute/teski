from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlmodel import Session, select
from models import Task, Reminder
from services.scoring import score, script_hint  # you already have these
from settings import DEFAULT_TIMEZONE

# Cooldowns per escalation level (so we don't nag too often)
COOLDOWNS = {
    "calm": timedelta(hours=24),
    "snark": timedelta(hours=12),
    "disappointed": timedelta(hours=4),
    "intervention": timedelta(hours=2),
}

def last_reminder_for_task(session: Session, task_id: str) -> Optional[Reminder]:
    return session.exec(
        select(Reminder)
        .where(Reminder.task_id == task_id)
        .order_by(Reminder.created_at.desc())
        .limit(1)
    ).first()

def due_for_reminder(now: datetime, last: Optional[Reminder], escalation: str) -> bool:
    if last is None:
        return True
    cd = COOLDOWNS.get(escalation, timedelta(hours=6))
    # Ensure last.created_at is offset-aware
    if last.created_at.tzinfo is None:
        last.created_at = last.created_at.replace(tzinfo=DEFAULT_TIMEZONE)
    else:
        last.created_at = last.created_at.astimezone(DEFAULT_TIMEZONE)
    return (now - last.created_at) >= cd

def build_message(title: str, escalation: str, hours_to_due: float) -> str:
    # Simple deterministic copy so frontend can display a clear line
    hrs = int(abs(round(hours_to_due)))
    if escalation == "intervention":
        return f"OVERDUE. ‘{title}’ needs action. Open it now; spend 25 minutes."
    if escalation == "disappointed":
        return f"{hrs}h left for ‘{title}’. Start now; one focused session."
    if escalation == "snark":
        return f"{hrs}h to go on ‘{title}’. Quick win time—kick it off."
    return f"Upcoming: ‘{title}’ in ~{hrs}h. Plan one small step today."

def maybe_create_reminder_for_task(session, task, persona):
    now = datetime.now(DEFAULT_TIMEZONE)
    # Ensure task.due_iso is offset-aware
    if task.due_iso.tzinfo is None:
        task.due_iso = task.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
    else:
        task.due_iso = task.due_iso.astimezone(DEFAULT_TIMEZONE)
    prio, esc = score(now, task.due_iso, task.status)

    # Skip very-distant tasks (priority 1 + > 7 days)
    if prio == 1 and (task.due_iso - now) > timedelta(days=7):
        return None

    last = last_reminder_for_task(session, task.id)
    if not due_for_reminder(now, last, esc):
        return None

    h2d = (task.due_iso - now).total_seconds() / 3600.0
    hints = script_hint(task.title, esc, h2d)
    msg = build_message(task.title, esc, h2d)

    rem = Reminder(
        task_id=task.id,
        escalation=esc,
        persona=persona,
        created_at=now,
        script_hints=msg if hints is None else f"{msg} || {hints}"
    )
    session.add(rem)
    session.commit()
    session.refresh(rem)
    return rem

def run_sweep(session: Session, persona: str = "teacher") -> tuple[int, int]:
    """
    Iterate all non-done tasks and create reminders where due.
    Returns: (checked_count, created_count)
    """
    tasks = session.exec(select(Task).where(Task.status != "done")).all()
    checked, created = 0, 0
    for t in tasks:
        checked += 1
        if maybe_create_reminder_for_task(session, t, persona):
            created += 1
    return checked, created
