from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.config import get_settings


_TEMPLATES = {
    "calm": {
        "default": [
            "Take a breath, then nudge this forward one small step.",
            "You’ve got the rhythm—focus on the next tiny win.",
            "Steady pace, steady progress. Keep going.",
        ],
        "warmup": [
            "Welcome back! Let’s warm up with one gentle review.",
            "Morning stretch for your brain—light and easy.",
        ],
    },
    "snark": {
        "default": [
            "Ready to outsmart yesterday’s mistake?",
            "Let’s prove procrastination wrong—again.",
            "Time to flex those neurons, hotshot.",
        ],
        "warmup": [
            "First card of the day—no pressure… okay, maybe a little.",
            "Coffee in one hand, comeback streak in the other.",
        ],
    },
    "coach": {
        "default": [
            "Set your feet, visualize the answer, deliver.",
            "We’re building reps—finish strong on this one.",
            "Keep your form tight; the results follow.",
        ],
        "warmup": [
            "Light drill to get the mind firing—let’s do this.",
            "Warm-up rep. Smooth execution, no strain.",
        ],
    },
    "encourager": {
        "default": [
            "I’m cheering from the sidelines—take it step by step.",
            "You learn fast. This card is yours.",
            "You’ve handled tougher—shine on this one too.",
        ],
        "warmup": [
            "Hey friend! Let’s ease in with a warm-up win.",
            "First review today—let’s make it a confident start.",
        ],
    },
}


def _is_warmup(context: Dict[str, Any]) -> bool:
    if context.get("warmup"):
        return True
    if context.get("first_review_of_day"):
        return True
    ts = context.get("timestamp")
    if isinstance(ts, datetime):
        prior = context.get("last_review_ts")
        if not prior or prior.date() != ts.date():
            return True
    return False


def get_persona_copy(persona: str | None, context: Dict[str, Any] | None = None) -> str:
    """Return a warm coaching message tailored to the persona and context."""

    context = context or {}
    persona_key = (persona or get_settings().PERSONA_DEFAULT).strip().lower()
    chosen = _TEMPLATES.get(persona_key, _TEMPLATES["calm"])

    bank = chosen["warmup"] if _is_warmup(context) else chosen["default"]
    if not bank:
        bank = _TEMPLATES["calm"]["default"]
    # Rotate deterministically using optional seed from context
    seed = str(context.get("concept") or context.get("task_id") or context.get("user_id") or "")
    index = abs(hash(seed)) % len(bank) if seed else 0
    return bank[index]
