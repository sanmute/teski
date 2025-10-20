from __future__ import annotations

import math
import re
from difflib import SequenceMatcher
from typing import Dict, Optional

NUMERIC_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?", re.IGNORECASE)
UNIT_RE = re.compile(
    r"\b(?:[mkgtp]?m|s|kg|n|j|hz|pa|c|°c|°f|%|amp|a|v|w|mol|l|g|rad|deg)\b",
    re.IGNORECASE,
)


def _lev_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a or "", b or "").ratio()


def _to_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_number(text: str) -> Optional[float]:
    if not text:
        return None
    match = NUMERIC_RE.search(text)
    if not match:
        return None
    return _to_float(match.group(0))


def _extract_unit(text: str) -> Optional[str]:
    if not text:
        return None
    match = UNIT_RE.search(text)
    if not match:
        return None
    return match.group(0).lower()


def extract_units(text: str) -> set[str]:
    """Return all unit tokens found in text (normalized to lowercase)."""
    if not text:
        return set()
    return {match.group(0).lower() for match in UNIT_RE.finditer(text)}


def classify_mistake(
    prompt_text: str,
    user_answer: Optional[str],
    correct_answer: Optional[str],
    context: Dict[str, object] | None = None,
) -> str:
    context = context or {}
    ua = (user_answer or "").strip()
    ca = (correct_answer or "").strip()

    user_num = _first_number(ua)
    correct_num = _first_number(ca)
    expected_value = context.get("expected_value")
    if expected_value is not None:
        try:
            correct_num = float(expected_value)
        except (TypeError, ValueError):
            pass

    unit_expected = context.get("unit_expected")
    unit_received = context.get("unit_received")
    if context.get("unit_mismatch"):
        return "unit"

    if user_num is not None and correct_num is not None:
        if user_num != 0 and correct_num != 0 and math.isfinite(user_num) and math.isfinite(correct_num):
            if math.isclose(abs(user_num), abs(correct_num), rel_tol=1e-6) and (user_num * correct_num) < 0:
                return "sign"
            if math.isclose(user_num, correct_num, rel_tol=0.001, abs_tol=0.01):
                return "rounding"
            if math.isclose(user_num, correct_num, rel_tol=0.05, abs_tol=1e-9):
                return "near_miss"
        rel_error = context.get("relative_error")
        if rel_error is None:
            baseline = abs(correct_num) if correct_num != 0 else 1.0
            rel_error = abs(user_num - correct_num) / baseline if math.isfinite(baseline) and baseline > 0 else None
        if rel_error is not None and rel_error < 0.02:
            return "rounding"

    if unit_expected and unit_received:
        if str(unit_expected).strip().lower() != str(unit_received).strip().lower():
            return "unit"

    user_unit = _extract_unit(ua)
    correct_unit = _extract_unit(ca)
    if correct_unit and user_unit and user_unit != correct_unit:
        return "unit"

    if _lev_ratio(ua.lower(), ca.lower()) >= 0.75:
        return "near_miss"

    keywords = context.get("concept_keywords")
    if isinstance(keywords, (list, tuple)):
        missing = [
            kw for kw in keywords if isinstance(kw, str) and kw.lower() not in ua.lower()
        ]
        if missing and len(missing) >= max(1, len(keywords) // 2):
            return "conceptual"

    if prompt_text and ua:
        if _lev_ratio(prompt_text.lower(), ua.lower()) < 0.3 and len(ua.split()) <= 2:
            return "conceptual"

    return "other"
