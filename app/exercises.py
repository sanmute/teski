from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import json
import re

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback when PyYAML missing
    yaml = None  # type: ignore

ALLOWED_TYPES = {"mcq", "numeric", "short_answer"}


@dataclass
class Exercise:
    id: str
    concept: str
    type: str
    question: str
    course: Optional[str] = None
    difficulty: int = 1
    keywords: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in ALLOWED_TYPES:
            raise ValueError(f"Unsupported exercise type: {self.type}")
        if not isinstance(self.keywords, list):
            self.keywords = list(self.keywords or [])


_EXERCISE_CACHE: Optional[List[Exercise]] = None
_FRONT_MATTER_PATTERN = re.compile(r"^---\s*$", re.MULTILINE)


def load_exercises(content_dir: str | Path = "content") -> List[Exercise]:
    """Load exercises from markdown files that include YAML front matter."""
    global _EXERCISE_CACHE
    if _EXERCISE_CACHE is not None:
        return _EXERCISE_CACHE

    directory = Path(content_dir)
    exercises: List[Exercise] = []
    if not directory.exists():
        _EXERCISE_CACHE = []
        return _EXERCISE_CACHE

    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, _body = _extract_front_matter(text)
        if not metadata:
            continue
        try:
            exercise = _exercise_from_metadata(metadata, path)
        except Exception as exc:  # pragma: no cover - invalid content
            raise ValueError(f"Failed to load exercise from {path}: {exc}") from exc
        exercises.append(exercise)

    _EXERCISE_CACHE = exercises
    return exercises


def _extract_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    """Return (metadata, body) from a markdown file with YAML front matter."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("\n")
    closing_index = None
    for idx in range(1, len(parts)):
        if parts[idx].strip() == "---":
            closing_index = idx
            break
    if closing_index is None:
        return {}, text

    yaml_text = "\n".join(parts[1:closing_index])
    body = "\n".join(parts[closing_index + 1 :])
    if yaml:
        data = yaml.safe_load(yaml_text) or {}
    else:
        data = _minimal_yaml_parser(yaml_text)
    if not isinstance(data, dict):
        raise ValueError("Front matter must decode to a mapping")
    return data, body


def _minimal_yaml_parser(text: str) -> Dict[str, Any]:
    """Very small YAML subset parser used when PyYAML is unavailable."""
    result: Dict[str, Any] = {}
    current_key = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("  -") and current_key:
            result.setdefault(current_key, []).append(line.split("-", 1)[1].strip())
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            elif value:
                result[key] = value
            else:
                current_key = key
                result.setdefault(key, [])
    return result


def _exercise_from_metadata(meta: Dict[str, Any], path: Path) -> Exercise:
    required = ["id", "concept", "type", "question"]
    for key in required:
        if key not in meta:
            raise ValueError(f"Exercise {path} missing required key '{key}'")

    course = meta.get("course")
    difficulty = int(meta.get("difficulty", 1))
    keywords = meta.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    used_keys = set(required + ["course", "difficulty", "keywords"])
    remaining = {k: v for k, v in meta.items() if k not in used_keys}
    return Exercise(
        id=str(meta["id"]),
        concept=str(meta["concept"]),
        type=str(meta["type"]),
        question=str(meta["question"]).strip(),
        course=str(course) if course else None,
        difficulty=difficulty,
        keywords=list(keywords),
        meta=remaining,
    )


# -- Graders ----------------------------------------------------------------- #


def grade_mcq(payload: Dict[str, Any], exercise: Exercise) -> Tuple[bool, Dict[str, Any]]:
    choice_index = payload.get("choice")
    if not isinstance(choice_index, int):
        return False, {"error": "choice index required"}

    choices = exercise.meta.get("choices") or []
    if not isinstance(choices, list) or not choices:
        return False, {"error": "exercise has no choices configured"}

    if not 0 <= choice_index < len(choices):
        return False, {"error": "choice out of range", "choices": len(choices)}

    selected = choices[choice_index]
    correct_choice = next((idx for idx, c in enumerate(choices) if c.get("correct")), None)
    ok = bool(selected.get("correct"))
    info: Dict[str, Any] = {"selected": choice_index}
    if correct_choice is not None:
        info["correct_choice"] = correct_choice
    return ok, info


def grade_numeric(payload: Dict[str, Any], exercise: Exercise) -> Tuple[bool, Dict[str, Any]]:
    answer_meta = exercise.meta.get("answer") or {}
    try:
        expected_value = float(answer_meta["value"])
    except Exception:
        return False, {"error": "numeric answer misconfigured"}

    try:
        submitted_value = float(payload["value"])
    except Exception:
        return False, {"error": "numeric payload requires numeric 'value'"}

    tolerance = answer_meta.get("tolerance", "relative:0.01")
    tol_type, tol_amount = _parse_tolerance(tolerance)

    delta = abs(submitted_value - expected_value)
    ok = False
    if tol_type == "relative":
        baseline = abs(expected_value) if expected_value != 0 else 1.0
        ok = delta <= tol_amount * baseline
    else:
        ok = delta <= tol_amount

    info: Dict[str, Any] = {"submitted": submitted_value, "expected": expected_value}

    expected_unit = answer_meta.get("unit")
    received_unit = payload.get("unit")
    if expected_unit:
        info["unit_expected"] = expected_unit
        info["unit_received"] = received_unit
        if (received_unit or "").strip().lower() != expected_unit.strip().lower():
            ok = False
            info["unit_mismatch"] = True

    if not ok:
        info["delta"] = delta
    return ok, info


def _parse_tolerance(spec: Any) -> Tuple[str, float]:
    if isinstance(spec, (int, float)):
        return "abs", float(spec)
    if isinstance(spec, str):
        if ":" in spec:
            kind, val = spec.split(":", 1)
            try:
                return kind.strip(), float(val)
            except ValueError:
                return "relative", 0.01
        try:
            return "abs", float(spec)
        except ValueError:
            return "relative", 0.01
    return "relative", 0.01


def grade_short_answer(payload: Dict[str, Any], exercise: Exercise) -> Tuple[bool, Dict[str, Any]]:
    text = payload.get("text")
    if not isinstance(text, str):
        return False, {"error": "short answer requires 'text'"}

    rubric = exercise.meta.get("rubric") or {}
    text_lower = text.lower()
    info: Dict[str, Any] = {}

    must_include: Iterable[str] = rubric.get("must_include", [])
    missing = [token for token in must_include if token.lower() not in text_lower]

    synonyms: Dict[str, Iterable[str]] = rubric.get("synonyms", {})
    for target, alts in synonyms.items():
        if target in missing:
            if any(str(alt).lower() in text_lower for alt in alts):
                missing.remove(target)

    if missing:
        info["missing"] = missing
        return False, info

    must_not_include: Iterable[str] = rubric.get("must_not_include", [])
    present = [token for token in must_not_include if token.lower() in text_lower]
    if present:
        info["forbidden"] = present
        return False, info

    length_max = rubric.get("length_max")
    if length_max and len(text.split()) > int(length_max):
        info["too_long"] = len(text.split())
        return False, info

    return True, info


def grade(payload: Dict[str, Any], exercise: Exercise) -> Tuple[bool, Dict[str, Any]]:
    if exercise.type == "mcq":
        return grade_mcq(payload, exercise)
    if exercise.type == "numeric":
        return grade_numeric(payload, exercise)
    if exercise.type == "short_answer":
        return grade_short_answer(payload, exercise)
    raise ValueError(f"Unknown exercise type: {exercise.type}")
