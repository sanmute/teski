# >>> DETECTORS START
from __future__ import annotations

import math
import re
from typing import Any, Optional


def classify_numeric_near_miss(submitted: Any, truth: float, rel_tol: float = 0.05) -> bool:
    try:
        s = float(submitted)
    except Exception:
        return False
    if math.isnan(s) or math.isnan(truth):
        return False
    return abs(s - truth) <= max(rel_tol * abs(truth), 1e-9)


def classify_sign_flip(submitted: Any, truth: float, tol: float = 1e-9) -> bool:
    try:
        s = float(submitted)
    except Exception:
        return False
    return abs(abs(s) - abs(truth)) <= tol and (s * truth) < 0


_UNIT_RE = re.compile(r"(?P<value>[-+]?\d+(\.\d+)?(?:e[-+]?\d+)?)\s*(?P<unit>[A-Za-z/^\-·*]+)?")


def extract_unit(answer: str) -> Optional[str]:
    if not isinstance(answer, str):
        return None
    match = _UNIT_RE.search(answer.strip())
    if not match:
        return None
    unit = (match.group("unit") or "").strip()
    return unit or None


def classify_unit_confusion(submitted_text: str, expected_unit: Optional[str]) -> bool:
    if not expected_unit:
        return False
    submitted_unit = extract_unit(submitted_text or "")
    if not submitted_unit:
        return False

    def _norm(u: str) -> str:
        return u.replace("·", "*").replace("^1", "").lower()

    su = _norm(submitted_unit)
    eu = _norm(expected_unit)
    if su == eu:
        return False
    if su.replace("k", "") == eu or eu.replace("k", "") == su:
        return True
    return True
# <<< DETECTORS END
