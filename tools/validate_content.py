from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from app import exercises


def _validate_exercise(ex: exercises.Exercise) -> List[str]:
    errors: List[str] = []
    if not ex.id.strip():
        errors.append("exercise id cannot be empty")
    if not ex.question.strip():
        errors.append(f"{ex.id}: question text is empty")
    if ex.difficulty < 1:
        errors.append(f"{ex.id}: difficulty must be >= 1")

    if ex.type == "mcq":
        choices = ex.meta.get("choices")
        if not isinstance(choices, list) or not choices:
            errors.append(f"{ex.id}: mcq requires a non-empty choices list")
        elif not any(isinstance(choice, dict) and choice.get("correct") for choice in choices):
            errors.append(f"{ex.id}: mcq requires at least one correct choice")
    elif ex.type == "numeric":
        answer = ex.meta.get("answer")
        if not isinstance(answer, dict) or "value" not in answer:
            errors.append(f"{ex.id}: numeric exercise must define answer.value")
    elif ex.type == "short_answer":
        rubric = ex.meta.get("rubric")
        if not isinstance(rubric, dict):
            errors.append(f"{ex.id}: short_answer requires a rubric section")
    return errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate exercise content front matter.")
    parser.add_argument("--content", default="content", help="Content directory to scan (default: %(default)s)")
    args = parser.parse_args(argv)

    content_path = Path(args.content)
    if not content_path.exists():
        print(f"Content directory not found: {content_path}", file=sys.stderr)
        return 1

    exercises._EXERCISE_CACHE = None
    try:
        loaded = exercises.load_exercises(content_path)
    except Exception as exc:  # pragma: no cover - exercised via tests
        print(f"Failed to load exercises: {exc}", file=sys.stderr)
        return 1

    seen_ids = set()
    errors: List[str] = []
    for ex in loaded:
        if ex.id in seen_ids:
            errors.append(f"duplicate exercise id detected: {ex.id}")
        else:
            seen_ids.add(ex.id)
        errors.extend(_validate_exercise(ex))

    if errors:
        for err in errors:
            print(f"[ERROR] {err}", file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print(f"Validated {len(loaded)} exercise(s) in {content_path}.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
