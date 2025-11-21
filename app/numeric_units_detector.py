from __future__ import annotations

import math
import re
from typing import Any, Optional, Tuple

from app.mistake_types import MistakeInfo

NUMERIC_PATTERN = re.compile(r"^\s*([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)(?:\s*([a-zA-Z/]+))?\s*$")

_UNIT_SCALES = {
    "m": 1.0,
    "cm": 0.01,
    "mm": 0.001,
    "km": 1000.0,
    "s": 1.0,
    "ms": 0.001,
    "min": 60.0,
    "kg": 1.0,
    "g": 0.001,
}


def parse_value_and_unit(answer: Any) -> Tuple[Optional[float], Optional[str]]:
    """Parse answers like "12.5 m" or {"value": 3.2, "unit": "kg"} into (value, unit)."""
    if isinstance(answer, dict):
        value = answer.get("value") or answer.get("expected") or answer.get("submitted")
        unit = answer.get("unit") or answer.get("unit_hint")
        return _coerce_float(value), _normalize_unit(unit)

    if isinstance(answer, (int, float)):
        return float(answer), None

    if isinstance(answer, str):
        text = answer.strip()
        match = NUMERIC_PATTERN.match(text)
        if match:
            value = _coerce_float(match.group(1))
            unit = _normalize_unit(match.group(2))
            return value, unit
    return None, None


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _normalize_unit(unit: Any) -> Optional[str]:
    if not unit or not isinstance(unit, str):
        return None
    clean = unit.strip().lower()
    return clean or None


def compare_numeric_values(expected: float, given: float) -> dict:
    baseline = abs(expected) if expected != 0 else 1.0
    abs_diff = abs(given - expected)
    rel_diff = abs_diff / baseline if baseline > 0 else None
    sign_mismatch = (expected * given) < 0 if math.isfinite(expected) and math.isfinite(given) else False
    order_diff = None
    if expected != 0 and given != 0 and math.isfinite(expected) and math.isfinite(given):
        ratio = abs(given / expected)
        if ratio > 0:
            order_diff = round(math.log10(ratio))
    return {
        "abs_diff": abs_diff,
        "rel_diff": rel_diff,
        "sign_mismatch": sign_mismatch,
        "order_of_magnitude_diff": order_diff,
    }


def _convert(value: float, from_unit: str, to_unit: str) -> Optional[float]:
    if from_unit not in _UNIT_SCALES or to_unit not in _UNIT_SCALES:
        return None
    base_value = value * _UNIT_SCALES[from_unit]
    return base_value / _UNIT_SCALES[to_unit]


def detect_numeric_unit_mistake(
    expected_value: Optional[float],
    expected_unit: Optional[str],
    given_value: Optional[float],
    given_unit: Optional[str],
    tolerance: float = 0.01,
) -> Optional[MistakeInfo]:
    # Units first
    if expected_unit:
        if not given_unit:
            return MistakeInfo(family="units", subtype="missing_unit", severity="medium", is_near_miss=False)
        if given_unit != expected_unit:
            converted = None
            if expected_value is not None and given_value is not None:
                converted = _convert(given_value, given_unit, expected_unit)
            if converted is not None and math.isclose(converted, expected_value or 0, rel_tol=tolerance, abs_tol=tolerance):
                return MistakeInfo(family="units", subtype="conversion_error", severity="medium", is_near_miss=False)
            return MistakeInfo(family="units", subtype="wrong_unit", severity="medium", is_near_miss=False)

    if expected_value is None or given_value is None:
        return None

    metrics = compare_numeric_values(expected_value, given_value)
    rel_diff = metrics.get("rel_diff")
    sign_mismatch = metrics.get("sign_mismatch")
    order_diff = metrics.get("order_of_magnitude_diff")

    if sign_mismatch and math.isclose(abs(given_value), abs(expected_value), rel_tol=0.2, abs_tol=0.0001):
        return MistakeInfo(family="numeric", subtype="sign_error", severity="medium", is_near_miss=False)

    if rel_diff is not None and rel_diff <= tolerance:
        return MistakeInfo(family="numeric", subtype="rounding_error", severity="low", is_near_miss=True)

    if order_diff is not None and abs(order_diff) in {1, 2}:
        return MistakeInfo(family="numeric", subtype="large_magnitude_error", severity="high", is_near_miss=False)

    if rel_diff is not None and rel_diff <= 0.05:
        return MistakeInfo(family="numeric", subtype="small_precision_error", severity="low", is_near_miss=True)

    return None
