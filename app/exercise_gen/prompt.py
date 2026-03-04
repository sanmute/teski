"""Prompt builder for the AI exercise-generation agent.

This module contains pure string-building logic only — no API calls, no I/O.
The single public function ``build_generation_prompt`` assembles a structured
prompt that instructs a language model to produce one or more exercises in the
canonical YAML-front-matter + Markdown format used by the ``content/`` directory.

Output format contract (enforced by the prompt)
------------------------------------------------
The model must emit exactly ``count`` exercise blocks.  Each block looks like::

    ---
    id: <slug>
    concept: <short concept name>
    type: <mcq|numeric|short_answer>
    question: <full question text>
    difficulty: <1-5>
    skill_ids:
      - <skill_slug>
    keywords:
      - <keyword>
    # optional: course, domain, subdomain
    # type-specific keys follow …
    ---

    ## Answer
    <answer prose or value>

    ## Explanation
    <worked explanation>

Type-specific YAML keys
-----------------------
mcq
    ``choices`` — list of ``{text: str, correct: bool}``.
    Exactly one item must have ``correct: true``.

numeric
    ``answer`` — dict with ``value`` (float) and ``tolerance``
    (string, e.g. ``"relative:0.01"``).  Optionally ``unit``.

short_answer
    ``rubric`` — dict with ``must_include`` (list of required terms),
    optionally ``must_not_include`` (list of forbidden terms) and
    ``length_max`` (int, max word count).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Per-type YAML examples embedded verbatim in the prompt so the model can
# mirror the exact structure without guessing.
# ---------------------------------------------------------------------------

_MCQ_EXAMPLE = """\
---
id: kinematics-displacement-001
concept: displacement vs distance
type: mcq
question: "A car travels 4 km north then 3 km south. What is its displacement?"
difficulty: 2
skill_ids:
  - kinematics-vectors
keywords:
  - displacement
  - distance
  - vectors
course: physics-101
domain: Mechanics
choices:
  - text: "1 km north"
    correct: true
  - text: "7 km north"
    correct: false
  - text: "3 km south"
    correct: false
  - text: "4 km north"
    correct: false
---

## Answer
1 km north

## Explanation
Displacement is the straight-line vector from start to finish.  The car ends up
1 km (4 − 3) north of where it started, regardless of the total path length of 7 km.\
"""

_NUMERIC_EXAMPLE = """\
---
id: kinematics-velocity-001
concept: average velocity
type: numeric
question: "A cyclist covers 120 m in 15 s at constant speed. What is their speed in m/s?"
difficulty: 1
skill_ids:
  - kinematics-equations
keywords:
  - speed
  - velocity
  - constant motion
course: physics-101
domain: Mechanics
answer:
  value: 8.0
  tolerance: "relative:0.01"
  unit: "m/s"
---

## Answer
8.0 m/s

## Explanation
Average speed = distance / time = 120 m ÷ 15 s = 8.0 m/s.\
"""

_SHORT_ANSWER_EXAMPLE = """\
---
id: kinematics-newtons-first-001
concept: Newton's first law
type: short_answer
question: "In your own words, state Newton's first law of motion and give one everyday example."
difficulty: 2
skill_ids:
  - newtons-laws
keywords:
  - inertia
  - Newton's first law
  - rest
  - uniform motion
course: physics-101
domain: Mechanics
rubric:
  must_include:
    - inertia
    - net force
  must_not_include:
    - acceleration
  length_max: 80
---

## Answer
An object at rest stays at rest, and an object in motion stays in motion at
constant velocity, unless acted on by a net external force (inertia).

## Explanation
The key insight is that *no net force* is required to maintain constant velocity —
only to *change* it.  A book sitting on a table, or a hockey puck sliding on ice,
are everyday illustrations.\
"""

_EXAMPLE_BY_TYPE: dict[str, str] = {
    "mcq": _MCQ_EXAMPLE,
    "numeric": _NUMERIC_EXAMPLE,
    "short_answer": _SHORT_ANSWER_EXAMPLE,
}

# ---------------------------------------------------------------------------
# Type-specific constraint descriptions injected into the instructions block.
# ---------------------------------------------------------------------------

_TYPE_CONSTRAINTS: dict[str, str] = {
    "mcq": (
        "Each exercise MUST include a ``choices`` key in the YAML front matter.\n"
        "``choices`` is a YAML list of mappings, each with ``text`` (string) and\n"
        "``correct`` (boolean).  Exactly ONE choice per exercise must have\n"
        "``correct: true``.  Provide 3–5 plausible distractors."
    ),
    "numeric": (
        "Each exercise MUST include an ``answer`` mapping in the YAML front matter\n"
        "with the sub-keys:\n"
        "  ``value``     — the exact numeric answer as a float (e.g. 9.81)\n"
        "  ``tolerance`` — a string in the form ``\"relative:0.01\"`` (1 % tolerance)\n"
        "                  or ``\"abs:0.5\"`` (±0.5 absolute).  Default to\n"
        "                  ``\"relative:0.01\"`` when unsure.\n"
        "  ``unit``      — (optional) SI unit string, e.g. ``\"m/s\"``.\n"
        "The ``## Answer`` section must state the numeric value and unit."
    ),
    "short_answer": (
        "Each exercise MUST include a ``rubric`` mapping in the YAML front matter\n"
        "with:\n"
        "  ``must_include``     — list of 2–6 key terms the answer MUST contain\n"
        "  ``must_not_include`` — (optional) list of terms the answer must NOT use\n"
        "                        (e.g. circular definitions)\n"
        "  ``length_max``       — (optional) maximum word count for a valid answer\n"
        "The ``## Answer`` section must be a model answer that satisfies the rubric."
    ),
}

_DIFFICULTY_LABELS: dict[int, str] = {
    1: "very easy",
    2: "easy",
    3: "intermediate",
    4: "hard",
    5: "expert",
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_generation_prompt(
    topic: str,
    exercise_type: str,
    difficulty: int,
    count: int,
    course: str | None = None,
    domain: str | None = None,
    seed_text: str | None = None,
    language: str = "en",
) -> str:
    """Build a prompt that instructs a language model to generate exercises.

    The returned string is a ready-to-send user-turn message.  The caller is
    responsible for supplying an appropriate system prompt and making the API
    call.  This function performs no I/O and has no side effects.

    Parameters
    ----------
    topic:
        The subject matter for the exercises, e.g. ``"Newton's laws of motion"``
        or ``"compound interest"``.  Be as specific as you like.
    exercise_type:
        One of ``"mcq"``, ``"numeric"``, or ``"short_answer"``.  Must match a
        value from ``app.exercises.ALLOWED_TYPES``.
    difficulty:
        Integer from 1 (easiest) to 5 (hardest).  Guides the cognitive demand
        and vocabulary level of the generated questions.
    count:
        Number of distinct exercises to generate in a single response.
    course:
        Optional course identifier (e.g. ``"physics-101"``).  When provided it
        is injected into the YAML of each generated exercise.
    domain:
        Optional domain label (e.g. ``"Mechanics"``).  Used as context for the
        model and embedded in each exercise's YAML when provided.
    seed_text:
        Optional source material (e.g. a pasted exam question, textbook
        excerpt, or lecture note).  When present the model is instructed to
        base its exercises on this text rather than generating from scratch.
    language:
        BCP-47 language tag for the desired output language.  Defaults to
        ``"en"`` (English).

    Returns
    -------
    str
        A prompt string suitable for use as the ``user`` message in an
        Anthropic ``messages.create`` call.

    Raises
    ------
    ValueError
        If ``exercise_type`` is not one of the allowed values, or if
        ``difficulty`` is outside the range 1–5, or if ``count`` is less than 1.

    Examples
    --------
    >>> prompt = build_generation_prompt(
    ...     topic="ideal gas law",
    ...     exercise_type="numeric",
    ...     difficulty=3,
    ...     count=2,
    ...     course="chemistry-101",
    ... )
    >>> assert prompt.startswith("You are an expert")
    """
    _validate_args(exercise_type, difficulty, count)

    parts: list[str] = []

    # ------------------------------------------------------------------
    # 1. Role / task framing
    # ------------------------------------------------------------------
    type_label = exercise_type.upper().replace("_", " ")
    parts.append(
        f"You are an expert instructional designer.\n"
        f"Generate exactly {count} {type_label} exercise(s) "
        f"on the topic: **{topic}**."
    )

    # ------------------------------------------------------------------
    # 2. Optional context (course, domain, difficulty, language)
    # ------------------------------------------------------------------
    difficulty_label = _DIFFICULTY_LABELS[difficulty]
    context_lines: list[str] = [
        f"- Difficulty level: {difficulty} out of 5  ({difficulty_label})"
    ]
    if course:
        context_lines.append(f"- Course: {course}")
    if domain:
        context_lines.append(f"- Domain: {domain}")
    if language != "en":
        context_lines.append(
            f"- Output language: {language}  "
            "(write question, choices, answer, and explanation in this language)"
        )

    parts.append("Context:\n" + "\n".join(context_lines))

    # ------------------------------------------------------------------
    # 3. Seed text (if provided)
    # ------------------------------------------------------------------
    if seed_text:
        parts.append(
            "Base the exercises on the following source material.  "
            "You may quote, paraphrase, or derive questions directly from it, "
            "but every exercise must be self-contained (a student should not need "
            "the source text to answer it).\n\n"
            "--- SOURCE MATERIAL START ---\n"
            f"{seed_text.strip()}\n"
            "--- SOURCE MATERIAL END ---"
        )

    # ------------------------------------------------------------------
    # 4. Output format instructions
    # ------------------------------------------------------------------
    parts.append(
        "OUTPUT FORMAT — follow this exactly:\n\n"
        "Emit ONLY the exercise blocks described below.  "
        "Do NOT include any commentary, preamble, numbering, or text outside the blocks.\n\n"
        "Each exercise must be a Markdown document with YAML front matter:\n\n"
        "  • Open the front matter with a line containing exactly ``---``\n"
        "  • Close the front matter with a line containing exactly ``---``\n"
        "  • After the front matter, include a ``## Answer`` section and a\n"
        "    ``## Explanation`` section.\n"
        "  • Separate consecutive exercises with a blank line (the closing ``---``\n"
        "    of one block and the opening ``---`` of the next are sufficient).\n\n"
        "Required YAML keys for EVERY exercise:\n"
        "  id          — a short, unique kebab-case slug (e.g. ``topic-concept-NNN``)\n"
        "  concept     — a short noun phrase naming the tested concept\n"
        f"  type        — must be exactly ``{exercise_type}``\n"
        "  question    — the full question text (quote if it contains special chars)\n"
        f"  difficulty  — must be exactly {difficulty}\n"
        "  skill_ids   — YAML list of 1–3 kebab-case skill tags\n"
        "  keywords    — YAML list of 2–5 relevant keywords"
    )

    optional_keys: list[str] = []
    if course:
        optional_keys.append(f"  course      — include as ``{course}``")
    if domain:
        optional_keys.append(f"  domain      — include as ``{domain}``")
    optional_keys.append("  subdomain   — (optional) finer-grained sub-area")

    parts.append(
        "Optional YAML keys (include when relevant):\n" + "\n".join(optional_keys)
    )

    # ------------------------------------------------------------------
    # 5. Type-specific constraints
    # ------------------------------------------------------------------
    parts.append(
        f"Type-specific requirements for ``{exercise_type}``:\n\n"
        + _TYPE_CONSTRAINTS[exercise_type]
    )

    # ------------------------------------------------------------------
    # 6. Worked example for the requested type
    # ------------------------------------------------------------------
    parts.append(
        "Here is a complete example of the required format for this exercise type.  "
        "Match the structure exactly (including indentation and YAML list syntax):\n\n"
        "```markdown\n"
        + _EXAMPLE_BY_TYPE[exercise_type]
        + "\n```"
    )

    # ------------------------------------------------------------------
    # 7. Final instruction / reminder
    # ------------------------------------------------------------------
    reminder_lines = [
        f"Now generate exactly {count} {exercise_type} exercise(s) on **{topic}**.",
        f"Difficulty: {difficulty}/5.",
    ]
    if seed_text:
        reminder_lines.append("Base them on the source material provided above.")
    reminder_lines.append(
        "Output ONLY the raw Markdown blocks — no extra text before or after."
    )
    parts.append("\n".join(reminder_lines))

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_args(exercise_type: str, difficulty: int, count: int) -> None:
    """Raise ``ValueError`` for obviously invalid arguments.

    Parameters
    ----------
    exercise_type:
        Must be one of ``"mcq"``, ``"numeric"``, ``"short_answer"``.
    difficulty:
        Must be an integer in the range 1–5 inclusive.
    count:
        Must be a positive integer.
    """
    allowed = {"mcq", "numeric", "short_answer"}
    if exercise_type not in allowed:
        raise ValueError(
            f"exercise_type must be one of {sorted(allowed)!r}, got {exercise_type!r}"
        )
    if not (1 <= difficulty <= 5):
        raise ValueError(f"difficulty must be between 1 and 5, got {difficulty!r}")
    if count < 1:
        raise ValueError(f"count must be at least 1, got {count!r}")
