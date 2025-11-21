from __future__ import annotations

from typing import Any, Optional

from app.exercises import Exercise
from app.generic_mistake_detector import detect_generic_mistake
from app.math_mistake_detector import detect_math_mistake_type
from app.mistake_types import MistakeInfo
from app.numeric_units_detector import detect_numeric_unit_mistake, parse_value_and_unit

try:
    from app.python_mistake_detector import detect_python_mistake_type
except Exception:  # pragma: no cover - optional module
    detect_python_mistake_type = None  # type: ignore


def _infer_domain(exercise: Exercise) -> str:
    if getattr(exercise, "domain", None):
        return exercise.domain.lower()
    meta_domain = (exercise.meta or {}).get("domain") if hasattr(exercise, "meta") else None
    if isinstance(meta_domain, str) and meta_domain.strip():
        return meta_domain.strip().lower()
    skill_text = " ".join(getattr(exercise, "skill_ids", []) or []).lower()
    if any(token in skill_text for token in ["python", "py_"]):
        return "python"
    if any(token in skill_text for token in ["calc", "alg", "math"]):
        return "math"
    return "general"


def diagnose_mistake(exercise: Exercise, user_answer: str, correct_answer: Any) -> Optional[MistakeInfo]:
    domain = _infer_domain(exercise)

    if domain == "python" and detect_python_mistake_type:
        info = detect_python_mistake_type(exercise, user_answer, correct_answer)
        if info:
            return info

    if domain == "math":
        info = detect_math_mistake_type(exercise, user_answer, correct_answer, getattr(exercise, "skill_ids", []) or [])
        if info:
            return info

    # Cross-domain numeric/unit detector for any numeric-like content
    if exercise.type.lower() in {"numeric"} or _looks_numericish(user_answer, correct_answer):
        exp_val, exp_unit = parse_value_and_unit(correct_answer)
        given_val, given_unit = parse_value_and_unit(user_answer)
        info = detect_numeric_unit_mistake(exp_val, exp_unit, given_val, given_unit)
        if info:
            return info

    info = detect_generic_mistake(exercise, user_answer, correct_answer)
    if info:
        return info

    return MistakeInfo(family="behavioral", subtype="pure_guess", severity="low", is_near_miss=False)


def _looks_numericish(user_answer: Any, correct_answer: Any) -> bool:
    text = f"{user_answer} {correct_answer}".lower()
    return any(ch.isdigit() for ch in text)
