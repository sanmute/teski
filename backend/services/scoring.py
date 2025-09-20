from __future__ import annotations
from datetime import datetime
from typing import Tuple, Literal
from ..settings import DEFAULT_TIMEZONE

Escalation = Literal["calm", "snark", "disappointed", "intervention"]


def _ensure_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=DEFAULT_TIMEZONE)
    return dt.astimezone(DEFAULT_TIMEZONE)


def hours_to_due(now_dt: datetime, due_dt: datetime) -> float:
    due_local = _ensure_local(due_dt)
    now_local = _ensure_local(now_dt)
    delta = due_local - now_local
    return delta.total_seconds() / 3600.0


def score(now_dt: datetime, due_dt: datetime, status: str) -> Tuple[int, Escalation]:
    h = hours_to_due(now_dt, due_dt)

    if status == "done":
        return 1, "calm"

    if h < 0:
        return 3, "intervention"  # overdue
    if h <= 24:
        return 3, "disappointed"  # same-day
    if h <= 72:
        return 2, "snark"         # this week
    return 1, "calm"              # later

# services/scoring.py
from .topic_matcher import match_topics, merge_resources, merge_practice_prompts

def script_hint(title: str, escalation: str, hours_left: float, notes: str = "") -> list[str]:
    # 1) find relevant topics (multiple)
    ranked = match_topics(title, notes, max_topics=4)
    topic_ids = [tid for tid, _ in ranked]

    # 2) pick resources (merged top-3) + add one practice prompt if available
    resources = merge_resources(topic_ids, limit=3)
    prompts = merge_practice_prompts(topic_ids, limit=1)

    hints: list[str] = []

    # escalation seasoning (keep your existing tone rules; example below)
    if hours_left <= 24:
        hints.append("Clock’s ticking. Start now; we’ll keep it tight and focused.")

    # resources as “why-enabled” bullets
    for r in resources:
        t = r.get("type","").capitalize()
        hints.append(f"{t}: {r['title']} — {r['url']}")

    for p in prompts:
        hints.append(f"Practice: {p['prompt']}")

    return hints
