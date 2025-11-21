from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel

from app.config import get_settings


class PersonaReaction(BaseModel):
    persona: str
    intensity: str
    mood: str
    message: str
    tags: List[str] = []


PERSONA_CHOICES = ["calm", "snark", "hype", "professor"]


_MESSAGES: Dict[str, Dict[str, str]] = {
    "calm": {
        "correct_big_win": "Nice work on that tough one. Keep steady.",
        "correct_streak": "That's another one. Momentum feels good, right?",
        "correct_after_mistake": "See? Adjust, try again, succeed.",
        "correct_normal": "Smooth. Keep this pace.",
        "incorrect_near_miss": "Very close. One tiny detail left.",
        "incorrect_review_regression": "This one’s stubborn, but you’re stronger than it.",
        "incorrect_streak_broken": "Take a breath. Reset and go again.",
        "incorrect_general": "That attempt missed, but now you know what to fix.",
    },
    "snark": {
        "correct_big_win": "Look at you, flexing on the hard stuff.",
        "correct_streak": "Hot streak unlocked. Don’t jinx it.",
        "correct_after_mistake": "Redemption arc deployed.",
        "correct_normal": "Alright, alright, you do know this.",
        "incorrect_near_miss": "You almost had it. Almost.",
        "incorrect_review_regression": "Déjà vu? Let’s actually beat it this time.",
        "incorrect_streak_broken": "Streak broke, ego intact? Cool, try again.",
        "incorrect_general": "That’s a miss. Reset and go smarter.",
    },
    "hype": {
        "correct_big_win": "Yes! Big swing landed!",
        "correct_streak": "You’re on fire. Keep it rolling.",
        "correct_after_mistake": "Bounce-back energy! Love to see it.",
        "correct_normal": "Great hit. Next one!",
        "incorrect_near_miss": "So close! Quick tweak and it’s yours.",
        "incorrect_review_regression": "Old foe, but you’ll outwork it.",
        "incorrect_streak_broken": "Shake it off—momentum comes back fast.",
        "incorrect_general": "That one slipped. You’ve got plenty more in you.",
    },
    "professor": {
        "correct_big_win": "A rigorous solution to a difficult prompt. Well done.",
        "correct_streak": "Consistent accuracy builds mastery. Continue.",
        "correct_after_mistake": "Correction noted. That adjustment worked.",
        "correct_normal": "Answer accepted. Proceed.",
        "incorrect_near_miss": "You were within striking distance. Examine the detail.",
        "incorrect_review_regression": "This concept still needs reinforcement. Review once more.",
        "incorrect_streak_broken": "Sequence reset. Reflect, then try again.",
        "incorrect_general": "Not quite. Diagnose the step that slipped.",
    },
}


def _normalize_persona(persona: Optional[str]) -> str:
    if not persona:
        return get_settings().PERSONA_DEFAULT
    key = persona.strip().lower()
    if key not in PERSONA_CHOICES:
        return get_settings().PERSONA_DEFAULT
    return key


def _pick_reaction_type(
    *,
    is_correct: bool,
    mastery_delta: float,
    difficulty: int,
    mistake_type: Optional[str],
    streak_before: int,
    streak_after: int,
    is_review: bool,
) -> str:
    if is_correct:
        if mastery_delta >= 3 or difficulty >= 4:
            return "correct_big_win"
        if streak_after >= 3:
            return "correct_streak"
        if mistake_type:
            return "correct_after_mistake"
        return "correct_normal"

    subtype = (mistake_type or "").split(":", 1)[-1] if mistake_type else None
    if subtype == "near_miss":
        return "incorrect_near_miss"
    if is_review:
        return "incorrect_review_regression"
    if streak_before >= 3 and streak_after == 0:
        return "incorrect_streak_broken"
    return "incorrect_general"


def _intensity_for(reaction_type: str) -> str:
    if reaction_type in {"correct_big_win", "correct_streak"}:
        return "high"
    if reaction_type in {"incorrect_streak_broken", "incorrect_review_regression"}:
        return "medium"
    return "low"


def _mood_for(reaction_type: str, is_correct: bool) -> str:
    if is_correct:
        return "positive"
    if reaction_type in {"incorrect_streak_broken", "incorrect_review_regression"}:
        return "supportive"
    if reaction_type == "incorrect_general":
        return "neutral"
    return "supportive"


def generate_persona_reaction(
    *,
    persona: Optional[str],
    is_correct: bool,
    mastery_before: float,
    mastery_after: float,
    streak_before: int,
    streak_after: int,
    difficulty: int,
    mistake_type: Optional[str],
    is_review: bool,
) -> PersonaReaction:
    persona_key = _normalize_persona(persona)
    mastery_delta = mastery_after - mastery_before
    reaction_type = _pick_reaction_type(
        is_correct=is_correct,
        mastery_delta=mastery_delta,
        difficulty=difficulty,
        mistake_type=mistake_type,
        streak_before=streak_before,
        streak_after=streak_after,
        is_review=is_review,
    )

    template = _MESSAGES.get(persona_key, _MESSAGES["calm"])
    message = template.get(reaction_type, template["correct_normal" if is_correct else "incorrect_general"])

    tags: List[str] = []
    if mastery_delta > 0:
        tags.append("mastery_up")
    elif mastery_delta < 0:
        tags.append("mastery_down")
    if streak_after > streak_before and streak_after > 1:
        tags.append("streak_up")
    if streak_before >= 3 and streak_after == 0 and not is_correct:
        tags.append("streak_reset")
    if mistake_type:
        subtype = mistake_type.split(":", 1)[-1]
        tags.append(f"mistake_{subtype}")
    if is_review:
        tags.append("review_mode")

    return PersonaReaction(
        persona=persona_key,
        intensity=_intensity_for(reaction_type),
        mood=_mood_for(reaction_type, is_correct),
        message=message,
        tags=tags,
    )
