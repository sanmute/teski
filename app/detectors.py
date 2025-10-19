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

    if user_num is not None and correct_num is not None:
        if user_num != 0 and correct_num != 0 and math.isfinite(user_num) and math.isfinite(correct_num):
            if math.isclose(abs(user_num), abs(correct_num), rel_tol=1e-6) and (user_num * correct_num) < 0:
                return "sign"
            if math.isclose(user_num, correct_num, rel_tol=0.05, abs_tol=1e-9):
                return "near_miss"
            if math.isclose(user_num, correct_num, rel_tol=0.001, abs_tol=0.01):
                return "rounding"

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
