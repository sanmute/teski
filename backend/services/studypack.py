from __future__ import annotations
import json
from datetime import datetime
from typing import Dict, Any, List
from sqlmodel import Session, select
from models import Task
from models_studypack import StudyPack
from services.topic_map import TOPIC_MAP, resolve_topic

FALLBACK_RESOURCES = [
    {
        "type": "notes",
        "title": "How to break down a task",
        "url": "https://www.mindtools.com/akx2m8i/task-analysis",
        "why": "Simple steps to analyze tasks.",
    },
    {
        "type": "article",
        "title": "Timeboxing: 25-minute focus",
        "url": "https://www.interaction-design.org/literature/topics/timeboxing",
        "why": "Keep tight focus windows.",
    },
    {
        "type": "practice",
        "title": "Generic practice checklist",
        "url": "https://www.cs.cmu.edu/~./15110-s13/Wing07-ct.pdf",
        "why": "Framework for problem solving.",
    },
]

FALLBACK_PRACTICE = [
    {"prompt": "Define the task outcome in one sentence."},
    {"prompt": "List the first 3 concrete steps and do step 1 now."},
]

FALLBACK_TOPIC = "general.productivity"
from settings import DEFAULT_TIMEZONE

# Deterministic brief templates – persona + escalation aware
def make_brief(persona: str, escalation: str, hours_to_due: float, topic: str) -> str:
    ideas = TOPIC_MAP.get(topic, {}).get("ideas", [])
    k1 = ideas[0] if ideas else "Focus on core idea"
    k2 = ideas[1] if len(ideas) > 1 else "Do one concrete exercise"

    hrs = int(abs(round(hours_to_due)))
    if escalation == "intervention":
        base = f"You’re overdue. Start now. Two keys: {k1}; {k2}. Open the first link and do the first practice item."
    elif escalation == "disappointed":
        base = f"{hrs} hours left. Two keys: {k1}; {k2}. Begin with the first link, then attempt one practice problem."
    elif escalation == "snark":
        base = f"{hrs} hours. Shortcut plan: skim the first link at 1.25x, then do problems 1–3. Momentum beats perfection."
    else:
        base = f"Plenty of time, but future-you will thank you. Learn {k1}, then cement it with {k2}. Start with the first link."
    if persona == "roommate":
        return base.replace("Start", "Let’s start").replace("Begin", "Let’s begin")
    if persona == "sergeant":
        return base.replace(".", ". ").replace("  ", " ").upper()
    return base  # teacher default

def hours_to_due(now_dt, due_dt):
    if due_dt.tzinfo is None:
        due_local = due_dt.replace(tzinfo=DEFAULT_TIMEZONE)
    else:
        due_local = due_dt.astimezone(DEFAULT_TIMEZONE)
    now_local = now_dt if now_dt.tzinfo else now_dt.replace(tzinfo=DEFAULT_TIMEZONE)
    if now_local.tzinfo is not DEFAULT_TIMEZONE:
        now_local = now_local.astimezone(DEFAULT_TIMEZONE)
    delta = due_local - now_local
    return delta.total_seconds() / 3600.0

def build_study_pack_for_task(session: Session, task_id: str, persona: str = "teacher", escalation: str = "calm") -> Dict[str, Any]:
    task = session.exec(select(Task).where(Task.id == task_id)).first()
    if not task:
        raise ValueError("Task not found")

    try:
        topic = resolve_topic(task.title, task.notes) or fallback_topic(task)
        meta = TOPIC_MAP.get(topic)
        if not meta:
            raise KeyError("missing-topic")
        resources = [dict(r) for r in (meta.get("resources") or FALLBACK_RESOURCES)]
        practice = [dict(p) for p in (meta.get("practice") or FALLBACK_PRACTICE)]
    except Exception:
        topic = FALLBACK_TOPIC
        resources = [dict(r) for r in FALLBACK_RESOURCES]
        practice = [dict(p) for p in FALLBACK_PRACTICE]

    now = datetime.now(DEFAULT_TIMEZONE)
    if task.due_iso.tzinfo is None:
        task_due = task.due_iso.replace(tzinfo=DEFAULT_TIMEZONE)
    else:
        task_due = task.due_iso.astimezone(DEFAULT_TIMEZONE)
    task.due_iso = task_due
    h2d = hours_to_due(now, task_due)
    brief = make_brief(persona, escalation, h2d, topic)
    cta = "Open the first resource and start a 25-minute session."

    # persist / upsert
    sp = session.exec(
        select(StudyPack).where(StudyPack.task_id == task_id)
    ).first()
    if not sp:
        sp = StudyPack(
            task_id=task_id,
            topic=topic,
            resources_json=json.dumps(resources),
            practice_json=json.dumps(practice),
            brief_speech=brief,
            cta=cta,
            created_at=now,
            ttl_hours=24
        )
        session.add(sp)
    else:
        sp.topic = topic
        sp.resources_json = json.dumps(resources)
        sp.practice_json = json.dumps(practice)
        sp.brief_speech = brief
        sp.cta = cta
        sp.created_at = datetime.now(DEFAULT_TIMEZONE)
    session.commit()
    session.refresh(sp)

    return {
        "taskId": task_id,
        "topic": topic,
        "resources": resources,
        "practice": practice,
        "brief_speech": brief,
        "cta": cta,
        "created_at": sp.created_at.isoformat()
    }

def fallback_topic(task) -> str:
    t = (task.title + " " + (task.notes or "")).lower()
    if any(k in t for k in ["essay","thesis","draft","argument"]):
        return "writing.essay_argument"
    if any(k in t for k in ["bayes","conditional","probability","quiz"]):
        return "probability.bayes"
    if any(k in t for k in ["eigen","linear algebra","la "]):
        return "linear_algebra.eigenvalues"
    if any(k in t for k in ["fbd","free body","dynamics","forces"]):
        return "mech.dynamics.free_body"
    return "general.productivity"
