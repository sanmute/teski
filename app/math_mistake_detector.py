from __future__ import annotations

import math
import re
from typing import Any, Iterable, Optional

from app.mistake_types import MistakeInfo
from app.exercises import Exercise


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _extract_numeric(answer: Any) -> Optional[float]:
    if isinstance(answer, dict):
        for key in ("value", "submitted", "expected", "answer"):
            if key in answer:
                numeric = _as_float(answer[key])
                if numeric is not None:
                    return numeric
        # fall back to first primitive value
        for val in answer.values():
            numeric = _as_float(val)
            if numeric is not None:
                return numeric
    if isinstance(answer, (int, float)):
        return float(answer)
    if isinstance(answer, str):
        match = re.search(r"[-+]?\d+(?:\.\d+)?", answer)
        if match:
            return _as_float(match.group(0))
    return None


def _skill_matches(skill_ids: Iterable[str], *needles: str) -> bool:
    haystack = " ".join(skill_ids).lower()
    return any(needle in haystack for needle in needles)


def _looks_like_derivative_prompt(exercise: Exercise, skill_ids: list[str]) -> bool:
    text = f"{exercise.concept} {exercise.question} {' '.join(skill_ids)}".lower()
    return "derivative" in text or "deriv" in text or "chain rule" in text


def _derivative_rule_error(user_answer: str, correct_answer: str) -> bool:
    user_match = re.search(r"x\^\s*(\d+)", user_answer.replace(" ", ""))
    correct_match = re.search(r"x\^\s*(\d+)", correct_answer.replace(" ", ""))
    if user_match and correct_match:
        try:
            user_power = int(user_match.group(1))
            correct_power = int(correct_match.group(1))
            # common power-rule slip: n -> n+1 instead of n-1 (off by one or two)
            if abs(user_power - correct_power) in {1, 2}:
                return True
        except ValueError:
            pass
    # product/chain rule misses: correct has parentheses but user does not
    if "(" in correct_answer and ")" in correct_answer and "(" not in user_answer:
        return True
    return False


def detect_math_mistake_type(
    exercise: Exercise,
    user_answer: Any,
    correct_answer: Any,
    skill_ids: list[str] | None = None,
) -> Optional[MistakeInfo]:
    """
    Attempt to classify common algebra/calculus mistakes and return MistakeInfo.
    """

    skills = [s for s in (skill_ids or []) if s]
    user_value = _extract_numeric(user_answer)
    correct_value = _extract_numeric(correct_answer)
    numeric_applicable = exercise.type == "numeric" or _skill_matches(skills, "fraction", "limit", "unit")

    # --- Numeric heuristics -------------------------------------------------
    if numeric_applicable and user_value is not None and correct_value is not None:
        if math.isfinite(user_value) and math.isfinite(correct_value):
            if math.isclose(user_value, -correct_value, rel_tol=1e-6, abs_tol=1e-6):
                return MistakeInfo(family="math_concept", subtype="sign_error", severity="medium", is_near_miss=False)
            baseline = abs(correct_value) if correct_value != 0 else 1.0
            delta = abs(user_value - correct_value)
            if delta <= 0.005 * baseline:
                return MistakeInfo(
                    family="math_concept",
                    subtype="rounding_or_precision_error",
                    severity="low",
                    is_near_miss=True,
                )
            if _skill_matches(skills, "limit") and (math.isinf(correct_value) or math.isnan(correct_value)):
                return MistakeInfo(family="math_concept", subtype="limit_evaluation_error", severity="medium")

    # --- Derivative heuristics ---------------------------------------------
    user_text = str(user_answer or "").strip()
    correct_text = str(correct_answer or "").strip()
    if _looks_like_derivative_prompt(exercise, skills):
        if _derivative_rule_error(user_text, correct_text):
            return MistakeInfo(family="math_concept", subtype="derivative_rule_error", severity="high")

    # --- Limit heuristics ---------------------------------------------------
    if _skill_matches(skills, "limit"):
        if user_value is not None and correct_value is not None and math.isfinite(user_value) and not math.isfinite(correct_value):
            return MistakeInfo(family="math_concept", subtype="limit_evaluation_error", severity="medium")
        if "limit" in correct_text.lower() and "0/0" in user_text.replace(" ", ""):
            return MistakeInfo(family="math_concept", subtype="limit_evaluation_error", severity="medium")

    # --- Order of operations / distribution --------------------------------
    if _skill_matches(skills, "operations", "parentheses", "distribution", "simplification"):
        if "(" in correct_text and ")" in correct_text and "(" not in user_text:
            return MistakeInfo(family="math_concept", subtype="order_of_operations_error", severity="medium")
        if "+" in correct_text and correct_text.count("+") > user_text.count("+"):
            return MistakeInfo(family="math_concept", subtype="distribution_error", severity="medium")

    # --- Unit handling ------------------------------------------------------
    if _skill_matches(skills, "unit", "phys") and user_text and correct_text:
        # very light check: unit token missing from user answer
        unit_tokens = re.findall(r"[a-zA-Z]+/?[a-zA-Z]*", correct_text)
        if unit_tokens and not any(token in user_text for token in unit_tokens):
            return MistakeInfo(family="math_concept", subtype="unit_handling_error", severity="medium")

    if user_text and _skill_matches(skills, "simplification") and "x^" in user_text and "x^" in correct_text:
        return MistakeInfo(family="math_concept", subtype="algebraic_simplification_error", severity="medium")

    return None
