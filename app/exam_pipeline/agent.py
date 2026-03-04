"""Exam pipeline agent — downloads exam PDFs and generates practice exercises.

Each PDF is sent to Claude as a native ``document`` content block so the model
can read the full text without any client-side extraction.  The model returns a
JSON array of exercise objects which are validated and enriched with a
``raw_markdown`` field ready for writing to the ``content/`` directory.
"""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

import os

from anthropic import AsyncAnthropic
from fastapi import HTTPException

from app.exercises import ALLOWED_TYPES

_TIMEOUT = 180.0  # PDF analysis + exercise generation can take ~60–90 s

_anthropic_client: AsyncAnthropic | None = None


def _get_anthropic() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            timeout=_TIMEOUT,
        )
    return _anthropic_client

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)

_MODEL = "claude-opus-4-5"

_TYPE_MAP: dict[str, str] = {
    "mcq": "mcq",
    "multiple_choice": "mcq",
    "multiple choice": "mcq",
    "numeric": "numeric",
    "numerical": "numeric",
    "short_answer": "short_answer",
    "short answer": "short_answer",
    "short-answer": "short_answer",
    "open": "short_answer",
    "open_ended": "short_answer",
}
_MAX_TOKENS = 4096
_MAX_PDFS = 3
# Retry when fewer than this fraction of requested exercises are valid.
_MIN_VALID_FRACTION = 0.5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_from_pdfs(
    pdf_bytes_list: list[bytes],
    course_name: str,
    num_exercises: int = 10,
    exercise_types: list[str] | None = None,
    difficulty_range: tuple[int, int] = (1, 4),
) -> list[dict]:
    """Send exam PDFs to Claude and return validated exercise dicts.

    Parameters
    ----------
    pdf_bytes_list:
        Raw PDF bytes, one element per document.  At most 3 are used.
    course_name:
        Human-readable course name injected into the prompt and each exercise.
    num_exercises:
        Number of exercises to request from the model.
    exercise_types:
        List of allowed exercise types.  Defaults to all three types.
    difficulty_range:
        Inclusive ``(min, max)`` difficulty range on a 1–5 scale.

    Returns
    -------
    list[dict]
        Validated exercise dicts, each including a ``raw_markdown`` key
        containing the full ``.md`` file content ready to write to ``content/``.

    Raises
    ------
    HTTPException(502)
        If the Anthropic API call fails on the initial attempt and the retry.
    """
    if exercise_types is None:
        exercise_types = ["mcq", "numeric", "short_answer"]

    pdfs = pdf_bytes_list[:_MAX_PDFS]
    content_blocks = _build_content_blocks(
        pdfs, course_name, num_exercises, exercise_types, difficulty_range
    )

    raw = await _call_api(content_blocks)
    exercises = _parse_and_validate(raw, course_name)

    min_expected = max(1, int(num_exercises * _MIN_VALID_FRACTION))
    if len(exercises) < min_expected:
        logger.warning(
            "First attempt returned only %d/%d valid exercises; retrying.",
            len(exercises),
            num_exercises,
        )
        raw = await _call_api(content_blocks)
        exercises = _parse_and_validate(raw, course_name)

    return exercises


# ---------------------------------------------------------------------------
# Content block builders
# ---------------------------------------------------------------------------


def _build_content_blocks(
    pdfs: list[bytes],
    course_name: str,
    num_exercises: int,
    exercise_types: list[str],
    difficulty_range: tuple[int, int],
) -> list[dict]:
    blocks: list[dict] = []
    for pdf_bytes in pdfs:
        b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")
        blocks.append(
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64,
                },
            }
        )
    blocks.append(
        {
            "type": "text",
            "text": _build_prompt(
                course_name, num_exercises, exercise_types, difficulty_range
            ),
        }
    )
    return blocks


def _build_prompt(
    course_name: str,
    num_exercises: int,
    exercise_types: list[str],
    difficulty_range: tuple[int, int],
) -> str:
    course_slug = re.sub(r"[^a-z0-9]+", "-", course_name.lower()).strip("-")[:20]
    types_str = ", ".join(f'"{t}"' for t in exercise_types)
    return (
        f"You are an expert exam question author. The attached PDF(s) are past exam\n"
        f"papers for the course: {course_name}.\n\n"
        f"Generate exactly {num_exercises} practice exercises based on the question\n"
        f"styles, topics, and difficulty levels you see in these exams.\n\n"
        f"Use these exercise types: {types_str}\n"
        f"Difficulty range: {difficulty_range[0]}–{difficulty_range[1]} out of 5.\n\n"
        "Output ONLY a JSON array. Each object must have:\n"
        f'  id: string (e.g. "{course_slug}_001")\n'
        "  concept: string\n"
        '  type: "mcq" | "numeric" | "short_answer"\n'
        "  question: string\n"
        "  difficulty: integer 1–5\n"
        "  skill_ids: string[]\n"
        "  keywords: string[]\n"
        "  course: string\n"
        "  domain: string (the subject area)\n"
        "  meta: object containing:\n"
        '    - for mcq: { "choices": [{"text": str, "correct": bool}] }  — exactly 1 correct\n'
        '    - for numeric: { "answer": {"value": float, "tolerance": "relative:0.02"} }\n'
        '    - for short_answer: { "rubric": {"must_include": [str]} }\n'
        "  explanation: string (2–3 sentence explanation of the correct answer)\n\n"
        "Output raw JSON only. No markdown fences. No preamble."
    )


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------


async def _call_api(content_blocks: list[dict]) -> str:
    client = _get_anthropic()
    try:
        resp = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": content_blocks}],
        )
        pieces = [
            block.text
            for block in resp.content
            if getattr(block, "type", "") == "text"
        ]
        return "".join(pieces).strip()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Anthropic API call failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Parsing and validation
# ---------------------------------------------------------------------------


def _parse_and_validate(raw: str, course_name: str) -> list[dict]:
    raw = _strip_code_fence(raw)
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse JSON response: %s. Raw: %.200s", exc, raw)
        return []

    if not isinstance(items, list):
        logger.warning("Expected JSON array, got %s", type(items).__name__)
        return []

    valid: list[dict] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            logger.warning("Exercise %d is not a dict, skipping", idx)
            continue
        raw_type = str(item.get("type", "")).lower().strip()
        item["type"] = _TYPE_MAP.get(raw_type, raw_type)
        try:
            _validate_exercise(item, idx)
        except _ValidationError as exc:
            logger.warning("Skipping exercise %d: %s", idx, exc)
            continue
        if not item.get("course"):
            item["course"] = course_name
        item["raw_markdown"] = _build_raw_markdown(item)
        valid.append(item)

    return valid


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*\n(.*)\n```\s*$", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text


class _ValidationError(Exception):
    pass


def _validate_exercise(ex: dict[str, Any], idx: int) -> None:
    for key in ("id", "concept", "type", "question"):
        if not ex.get(key):
            raise _ValidationError(f"missing or empty required field '{key}'")

    if ex["type"] not in ALLOWED_TYPES:
        raise _ValidationError(f"invalid type '{ex['type']}'")

    diff = ex.get("difficulty")
    if not isinstance(diff, int) or not (1 <= diff <= 5):
        raise _ValidationError(f"difficulty must be int 1–5, got {diff!r}")

    meta = ex.get("meta") or {}
    if ex["type"] == "mcq":
        choices = meta.get("choices", [])
        if not choices:
            raise _ValidationError("mcq missing choices")
        correct_count = sum(
            1 for c in choices if isinstance(c, dict) and c.get("correct")
        )
        if correct_count != 1:
            raise _ValidationError(
                f"mcq must have exactly 1 correct choice, got {correct_count}"
            )


# ---------------------------------------------------------------------------
# raw_markdown builder
# ---------------------------------------------------------------------------


def _build_raw_markdown(ex: dict[str, Any]) -> str:
    exercise_type = ex.get("type", "")
    meta = ex.get("meta") or {}

    fm: dict[str, Any] = {
        "id": ex["id"],
        "concept": ex["concept"],
        "type": exercise_type,
        "question": ex["question"],
        "difficulty": ex["difficulty"],
        "skill_ids": ex.get("skill_ids") or [],
        "keywords": ex.get("keywords") or [],
    }
    if ex.get("course"):
        fm["course"] = ex["course"]
    if ex.get("domain"):
        fm["domain"] = ex["domain"]

    if exercise_type == "mcq":
        fm["choices"] = meta.get("choices", [])
    elif exercise_type == "numeric":
        fm["answer"] = meta.get("answer", {})
    elif exercise_type == "short_answer":
        fm["rubric"] = meta.get("rubric", {})

    if yaml is not None:
        yaml_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        yaml_str = _simple_yaml_dump(fm)

    answer_text = _derive_answer_text(ex)
    explanation = ex.get("explanation", "")

    return f"---\n{yaml_str}---\n\n## Answer\n{answer_text}\n\n## Explanation\n{explanation}\n"


def _derive_answer_text(ex: dict[str, Any]) -> str:
    meta = ex.get("meta") or {}
    t = ex.get("type", "")

    if t == "mcq":
        for choice in meta.get("choices", []):
            if isinstance(choice, dict) and choice.get("correct"):
                return str(choice.get("text", ""))
        return ""

    if t == "numeric":
        answer = meta.get("answer", {})
        val = answer.get("value", "")
        unit = answer.get("unit", "")
        return f"{val} {unit}".strip() if unit else str(val)

    if t == "short_answer":
        rubric = meta.get("rubric", {})
        must_include = rubric.get("must_include", [])
        if must_include:
            return "Key terms required: " + ", ".join(str(kw) for kw in must_include)
        return ""

    return ""


def _simple_yaml_dump(obj: Any, indent: int = 0) -> str:
    """Minimal YAML serialiser used when PyYAML is unavailable."""
    lines: list[str] = []
    prefix = "  " * indent

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_simple_yaml_dump(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {_yaml_scalar(v)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    marker = "- " if first else "  "
                    if isinstance(v, (dict, list)):
                        lines.append(f"{prefix}{marker}{k}:")
                        lines.append(_simple_yaml_dump(v, indent + 2))
                    else:
                        lines.append(f"{prefix}{marker}{k}: {_yaml_scalar(v)}")
                    first = False
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")

    return "\n".join(lines) + "\n" if lines else ""


def _yaml_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if any(c in s for c in ':#{}[]|>&*!,"'):
        return f'"{s.replace(chr(34), chr(92) + chr(34))}"'
    return s
