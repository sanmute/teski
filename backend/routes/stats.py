from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from db import get_session
from models_analytics import AnalyticsEvent

router = APIRouter(tags=["stats"])


def _window_bounds(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


def _group_by_date(events: List[AnalyticsEvent]) -> Dict[str, List[AnalyticsEvent]]:
    bucket: Dict[str, List[AnalyticsEvent]] = {}
    for ev in events:
        key = ev.ts.date().isoformat()
        bucket.setdefault(key, []).append(ev)
    return bucket


@router.get("/summary")
def summary(user_id: str = Query(...), days: int = Query(14, ge=1, le=90), session: Session = Depends(get_session)):
    since = _window_bounds(days)
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id, AnalyticsEvent.ts >= since)
    ).all()
    answered = sum(1 for ev in events if ev.event_type == "exercise_answer")
    correct = sum(1 for ev in events if ev.event_type == "exercise_correct")
    accuracy = (correct / answered) if answered else 0.0
    active_days = len(_group_by_date(events))
    last_at = max((ev.ts for ev in events), default=None)
    return {
        "ok": True,
        "user_id": user_id,
        "window_days": days,
        "totals": {
            "exercises_answered": answered,
            "exercises_correct": correct,
            "accuracy": accuracy,
            "active_days": active_days,
        },
        "last_activity_at": last_at.isoformat() if last_at else None,
    }


@router.get("/daily")
def daily(
    user_id: str = Query(...),
    days: int = Query(14, ge=1, le=90),
    session: Session = Depends(get_session),
):
    since = _window_bounds(days)
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id, AnalyticsEvent.ts >= since)
    ).all()
    grouped = _group_by_date(events)

    items = []
    today = date.today()
    for i in range(days):
        d = (today - timedelta(days=days - 1 - i)).isoformat()
        evs = grouped.get(d, [])
        answered = sum(1 for ev in evs if ev.event_type == "exercise_answer")
        correct = sum(1 for ev in evs if ev.event_type == "exercise_correct")
        acc = (correct / answered) if answered else None
        items.append(
            {
                "date": d,
                "exercises_answered": answered,
                "exercises_correct": correct,
                "accuracy": acc,
            }
        )
    return {"ok": True, "days": days, "items": items}


def _derive_course_key(ev: AnalyticsEvent) -> str:
    meta = ev.meta or {}
    topic = meta.get("topic")
    if topic:
        return str(topic)
    skills = meta.get("skill_ids") or []
    if skills:
        first = str(skills[0])
        return first.split("_", 1)[0] if "_" in first else first
    return "uncategorized"


@router.get("/by-course")
def by_course(
    user_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    session: Session = Depends(get_session),
):
    since = _window_bounds(days)
    events = session.exec(
        select(AnalyticsEvent).where(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.ts >= since,
            AnalyticsEvent.event_type.in_(["exercise_answer", "exercise_correct", "exercise_incorrect"]),
        )
    ).all()
    buckets: Dict[str, Dict[str, int]] = {}
    for ev in events:
        key = _derive_course_key(ev)
        bucket = buckets.setdefault(key, {"answered": 0, "correct": 0})
        if ev.event_type == "exercise_answer":
            bucket["answered"] += 1
        elif ev.event_type == "exercise_correct":
            bucket["correct"] += 1
            bucket["answered"] += 1  # ensure denominator counts
        else:
            bucket["answered"] += 1
    items = []
    for key, vals in buckets.items():
        ans = vals["answered"]
        cor = vals["correct"]
        acc = (cor / ans) if ans else 0.0
        items.append(
            {
                "course_key": key,
                "exercises_answered": ans,
                "exercises_correct": cor,
                "accuracy": acc,
            }
        )
    return {"ok": True, "days": days, "items": items}


@router.get("/insights")
def insights(
    user_id: str = Query(...),
    days: int = Query(14, ge=1, le=90),
    session: Session = Depends(get_session),
):
    since = _window_bounds(days)
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id, AnalyticsEvent.ts >= since)
    ).all()
    answered = sum(1 for ev in events if ev.event_type == "exercise_answer")
    correct = sum(1 for ev in events if ev.event_type == "exercise_correct")
    acc = (correct / answered) if answered else None

    # Top skill/course
    course_counts: Dict[str, int] = {}
    for ev in events:
        key = _derive_course_key(ev)
        course_counts[key] = course_counts.get(key, 0) + 1
    top_course = max(course_counts.items(), key=lambda x: x[1])[0] if course_counts else None

    items: List[Dict[str, Any]] = []
    if acc is not None:
        items.append({"kind": "accuracy", "text": f"Accuracy last {days}d: {acc:.0%}", "value": acc})
    if top_course:
        items.append({"kind": "top_course", "text": f"Most practiced area: {top_course}", "value": top_course})
    if not items:
        items.append({"kind": "note", "text": "Not enough data yet. Do a few exercises to unlock insights."})

    return {"ok": True, "days": days, "items": items}
