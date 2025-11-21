from __future__ import annotations

import math
from difflib import SequenceMatcher
from typing import Any, Optional

from app.exercises import Exercise
from app.mistake_types import MistakeInfo


def _lev_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a or "", b or "").ratio()


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def detect_generic_mistake(exercise: Exercise, user_answer: str, correct_answer: Any) -> Optional[MistakeInfo]:
    """Domain-agnostic lightweight detector covering MCQ, numeric, short-answer."""
    if not user_answer:
        return MistakeInfo(family="behavioral", subtype="pure_guess", severity="low", is_near_miss=False)

    if exercise.type.lower() in {"mcq", "multiple_choice"}:
        # If answer seems way off, treat as guess; otherwise plausible distractor.
        return MistakeInfo(family="reasoning", subtype="plausible_distractor", severity="medium", is_near_miss=False)

    # Numeric questions: near miss vs large error.
    user_val = _as_float(user_answer)
    correct_val = _as_float(correct_answer)
    if user_val is not None and correct_val is not None:
        baseline = abs(correct_val) if correct_val != 0 else 1.0
        delta = abs(user_val - correct_val)
        if delta <= 0.01 * baseline:
            return MistakeInfo(
                family="numeric",
                subtype="rounding_or_precision_error",
                severity="low",
                is_near_miss=True,
                raw_label=None,
            )
        if delta >= 10 * baseline:
            return MistakeInfo(family="numeric", subtype="large_magnitude_error", severity="high", is_near_miss=False)

    # Factual / short-answer similarity
    if exercise.domain and exercise.domain.lower() in {"history", "biology", "geography", "economics", "language"}:
        ca_str = str(correct_answer or "").strip()
        ratio = _lev_ratio(user_answer.lower(), ca_str.lower())
        if ratio >= 0.8:
            return MistakeInfo(
                family="factual",
                subtype="spelling_or_format",
                severity="low",
                is_near_miss=True,
            )
        return MistakeInfo(family="factual", subtype="incorrect_fact", severity="medium", is_near_miss=False)

    # Misread question heuristic: answer type mismatch
    if any(ch.isalpha() for ch in exercise.question) and user_answer.isdigit():
        return MistakeInfo(family="reading_comprehension", subtype="misread_question", severity="medium", is_near_miss=False)

    return None
