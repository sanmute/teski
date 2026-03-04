"""Exercise generation agent.

Orchestrates the full generate → parse → validate → return pipeline.
No prompting logic lives here (see prompt.py), and no schema definitions
(see schemas.py).

Public surface
--------------
generate_exercises(request)  — async; calls the LLM and returns parsed exercises.
save_exercises(request)      — sync; writes exercises to disk and busts the cache.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from ..config_feedback import get_feedback_settings  # noqa: F401 – imported for type clarity
from ..exercises import ALLOWED_TYPES, _extract_front_matter, invalidate_cache  # invalidate_cache added in next step
from ..feedback.clients import _get_anthropic
from .prompt import build_generation_prompt
from .schemas import GenerateRequest, GeneratedExercise, GenerateResponse, SaveRequest, SaveResponse

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 4096
_TEMPERATURE = 0.7
_SYSTEM_PROMPT = (
    "You are an expert instructional designer. "
    "Output only valid Markdown with YAML front matter exactly as instructed. "
    "No commentary, preamble, or text outside the exercise blocks."
)

# Fields that are promoted to top-level GeneratedExercise attributes;
# everything else lands in GeneratedExercise.meta.
_KNOWN_KEYS = frozenset({
    "id", "concept", "type", "question",
    "course", "domain", "subdomain",
    "difficulty", "skill_ids", "keywords",
})

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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_exercises(request: GenerateRequest) -> GenerateResponse:
    """Call the LLM, parse its output, validate, and return a GenerateResponse.

    Parameters
    ----------
    request:
        Validated GenerateRequest from the API layer.

    Returns
    -------
    GenerateResponse
        Contains all exercises that passed validation.  count_returned may be
        less than count_requested if the model produced fewer valid blocks.

    Raises
    ------
    HTTPException(502)
        If the LLM call fails on the first attempt and on the single retry.
    """
    # 1. Resolve seed_text according to A/B variant rules.
    if request.ab_variant == "topic_only":
        seed_text: str | None = None
    elif request.ab_variant == "seed_based":
        seed_text = request.seed_text
    else:
        seed_text = request.seed_text

    # 2. Build the user-turn prompt.
    prompt = build_generation_prompt(
        topic=request.topic,
        exercise_type=request.exercise_type,
        difficulty=request.difficulty,
        count=request.count,
        course=request.course,
        domain=request.domain,
        seed_text=seed_text,
        language=request.language,
    )

    # 3. Call the LLM (one automatic retry on failure).
    raw_text = await _call_with_retry(prompt)

    # 4. Parse and validate individual exercise blocks.
    exercises = _parse_response(raw_text)

    return GenerateResponse(
        exercises=exercises,
        count_requested=request.count,
        count_returned=len(exercises),
        ab_variant=request.ab_variant,
    )


def save_exercises(request: SaveRequest) -> SaveResponse:
    """Write each GeneratedExercise to ``{content_dir}/{id}.md``.

    Skips any exercise whose target file already exists (appends the id to
    ``skipped`` rather than overwriting).  After at least one file has been
    written, invalidates the in-process exercise cache so that subsequent
    ``load_exercises()`` calls pick up the new files.

    Parameters
    ----------
    request:
        SaveRequest containing the exercises to persist and the target directory.

    Returns
    -------
    SaveResponse
        ``saved`` — filenames actually written.
        ``skipped`` — exercise ids whose files already existed.
    """
    content_dir = Path(request.content_dir)
    content_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    skipped: list[str] = []

    for exercise in request.exercises:
        filename = f"{exercise.id}.md"
        path = content_dir / filename
        if path.exists():
            skipped.append(exercise.id)
            logger.debug("save_exercises: skipping %s (already exists)", filename)
            continue
        path.write_text(exercise.raw_markdown, encoding="utf-8")
        saved.append(filename)
        logger.info("save_exercises: wrote %s", path)

    if saved:
        invalidate_cache()

    return SaveResponse(saved=saved, skipped=skipped)


# ---------------------------------------------------------------------------
# LLM call helper
# ---------------------------------------------------------------------------


async def _call_with_retry(prompt: str) -> str:
    """Call the Anthropic API with a single automatic retry.

    Uses the shared AsyncAnthropic singleton from app.feedback.clients so no
    extra clients are created.  Parameters differ from call_anthropic() —
    specifically max_tokens=4096 and a generation-appropriate system prompt.

    Raises
    ------
    HTTPException(502)
        After two consecutive failures.
    """
    client = _get_anthropic()

    async def _once() -> str:
        resp = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            temperature=_TEMPERATURE,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        pieces = [
            block.text
            for block in resp.content
            if getattr(block, "type", "") == "text"
        ]
        return "".join(pieces).strip()

    try:
        return await _once()
    except Exception as exc:
        logger.warning("Exercise generation: first attempt failed (%s), retrying", exc)

    try:
        return await _once()
    except Exception as exc:
        logger.error("Exercise generation: retry also failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM call failed during exercise generation") from exc


# ---------------------------------------------------------------------------
# Parsing pipeline
# ---------------------------------------------------------------------------


def _parse_response(raw: str) -> list[GeneratedExercise]:
    """Orchestrate block extraction, front-matter parsing, and validation.

    Invalid blocks are skipped with a warning rather than raising, so a
    partially-valid response still returns whatever exercises passed.
    """
    cleaned = _strip_code_fence(raw)
    blocks = _split_exercise_blocks(cleaned)

    if not blocks:
        logger.warning("_parse_response: no exercise blocks found in LLM output")
        return []

    exercises: list[GeneratedExercise] = []
    for i, block in enumerate(blocks):
        try:
            meta, _body = _extract_front_matter(block)
            if not meta:
                logger.warning("Block %d: empty front matter, skipping", i)
                continue
            exercise = _build_exercise(meta, raw_markdown=block)
            _validate_exercise(exercise, block_index=i)
            exercises.append(exercise)
        except _ValidationError as exc:
            logger.warning("Block %d: validation failed — %s, skipping", i, exc)
        except Exception as exc:
            logger.warning("Block %d: parse error — %s, skipping", i, exc)

    return exercises


def _strip_code_fence(text: str) -> str:
    """Remove a leading/trailing ``` or ```markdown code fence if present.

    Models occasionally wrap their output in a fenced code block despite being
    asked not to.  This makes block-splitting robust to that pattern.
    """
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _split_exercise_blocks(text: str) -> list[str]:
    """Split raw text into individual exercise document strings.

    The model is instructed to emit blocks of the form::

        ---
        <yaml>
        ---
        <markdown body>

    Multiple consecutive blocks are separated by blank lines (the ``---``
    markers are sufficient delimiters).  ``---`` lines appear in pairs:
    the first opens the front matter, the second closes it.  Everything
    between the closing ``---`` of one block and the opening ``---`` of the
    next is the body of the preceding block.

    Returns
    -------
    list[str]
        Each string is a complete, self-contained exercise document starting
        with ``---``, ready to be fed to ``_extract_front_matter``.
    """
    lines = text.split("\n")
    sep_indices = [i for i, line in enumerate(lines) if line.strip() == "---"]

    blocks: list[str] = []
    # Separators pair up: open at even positions (0, 2, 4…), close at odd.
    i = 0
    while i + 1 < len(sep_indices):
        open_idx = sep_indices[i]
        close_idx = sep_indices[i + 1]
        next_open_idx = sep_indices[i + 2] if i + 2 < len(sep_indices) else len(lines)

        # Include everything from the opening --- through the body up to
        # (but not including) the next block's opening ---.
        body_lines = lines[close_idx + 1 : next_open_idx]
        doc = "\n".join(lines[open_idx : close_idx + 1] + body_lines).strip()
        if doc:
            blocks.append(doc)
        i += 2

    return blocks


def _build_exercise(meta: dict[str, Any], raw_markdown: str) -> GeneratedExercise:
    """Map a parsed YAML metadata dict to a GeneratedExercise.

    Known fields are promoted to named attributes.  All remaining keys (the
    type-specific ones: choices, answer, rubric, and anything else the model
    added) land in ``meta``.
    """
    skill_ids: list[str] = meta.get("skill_ids") or []
    if isinstance(skill_ids, str):
        skill_ids = [s.strip() for s in skill_ids.split(",") if s.strip()]

    keywords: list[str] = meta.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    extra_meta = {k: v for k, v in meta.items() if k not in _KNOWN_KEYS}

    raw_type = str(meta.get("type", "")).lower().strip()
    normalised_type = _TYPE_MAP.get(raw_type, raw_type)

    # Patch the YAML front matter in raw_markdown so the saved file uses the
    # normalised type (e.g. "multiple_choice" → "mcq").
    if raw_type != normalised_type:
        import re as _re
        raw_markdown = _re.sub(
            r"(?m)^(type:\s*)" + _re.escape(str(meta.get("type", ""))),
            r"\g<1>" + normalised_type,
            raw_markdown,
        )

    return GeneratedExercise(
        id=str(meta["id"]),
        concept=str(meta["concept"]),
        type=normalised_type,
        question=str(meta["question"]).strip(),
        difficulty=int(meta.get("difficulty", 1)),
        skill_ids=list(skill_ids),
        keywords=list(keywords),
        course=str(meta["course"]) if meta.get("course") else None,
        domain=str(meta["domain"]) if meta.get("domain") else None,
        subdomain=str(meta["subdomain"]) if meta.get("subdomain") else None,
        meta=extra_meta,
        raw_markdown=raw_markdown,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class _ValidationError(Exception):
    """Raised internally when a parsed exercise block fails structural checks."""


def _validate_exercise(exercise: GeneratedExercise, block_index: int) -> None:
    """Raise _ValidationError if the exercise violates any structural rule.

    Checks performed
    ----------------
    - All four required fields are non-empty strings.
    - ``type`` is one of the ALLOWED_TYPES.
    - ``difficulty`` is in the range 1–5.
    - For ``mcq``: ``choices`` list present and exactly one entry is correct.
    """
    for attr in ("id", "concept", "type", "question"):
        if not getattr(exercise, attr, None):
            raise _ValidationError(f"missing required field '{attr}'")

    if exercise.type not in ALLOWED_TYPES:
        raise _ValidationError(
            f"type '{exercise.type}' not in allowed set {sorted(ALLOWED_TYPES)}"
        )

    if not (1 <= exercise.difficulty <= 5):
        raise _ValidationError(
            f"difficulty {exercise.difficulty!r} is outside the valid range 1–5"
        )

    if exercise.type == "mcq":
        choices = exercise.meta.get("choices")
        if not isinstance(choices, list) or not choices:
            raise _ValidationError("mcq exercise is missing the 'choices' list in meta")
        correct_count = sum(
            1 for c in choices if isinstance(c, dict) and c.get("correct")
        )
        if correct_count != 1:
            raise _ValidationError(
                f"mcq exercise must have exactly 1 correct choice, found {correct_count}"
            )
