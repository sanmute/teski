from __future__ import annotations

import re
from typing import Any, Optional

from app.exercises import Exercise
from app.mistake_types import MistakeInfo


def detect_python_mistake_type(exercise: Exercise, user_answer: str, correct_answer: Any) -> Optional[MistakeInfo]:
    """Lightweight Python mistake classifier."""
    text = user_answer or ""
    lowered = text.lower()
    if "indent" in lowered or text.startswith(" ") and "for" in lowered:
        return MistakeInfo(family="python_syntax", subtype="indentation_error", severity="high", is_near_miss=False)
    if "syntaxerror" in lowered or "syntax error" in lowered:
        return MistakeInfo(family="python_syntax", subtype="syntax_error", severity="medium", is_near_miss=False)
    if re.search(r"print\\s*[,\\(]", lowered) and "python 3" in (exercise.question or "").lower():
        return MistakeInfo(family="python_syntax", subtype="print_function_error", severity="medium", is_near_miss=False)
    if "off by one" in lowered or "range(" in lowered and ("]" in text or")" in text):
        return MistakeInfo(family="python_logic", subtype="off_by_one", severity="medium", is_near_miss=False)
    return None
