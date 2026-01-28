from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

from sqlmodel import Session
from pydantic import BaseModel, Field, ValidationError, field_validator

from models_exercise import Exercise


class ExerciseSpec(BaseModel):
    id: str
    question_text: str
    type: str = Field(alias="type")
    choices: List[str] | None = None
    correct_answer: str
    difficulty: int = 1
    skill_ids: List[str] = Field(default_factory=list)
    solution_explanation: str | None = None
    hint: str | None = None
    metadata: Dict[str, object] | None = None

    @field_validator("type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        allowed = {"multiple_choice", "short_answer"}
        if v not in allowed:
            raise ValueError(f"type must be one of {sorted(allowed)}")
        return v

    @field_validator("choices")
    @classmethod
    def _choices_required_for_mcq(cls, v, info):
        if info.data.get("type") == "multiple_choice":
            if not v or not isinstance(v, list):
                raise ValueError("choices must be provided for multiple_choice")
        return v


@dataclass
class SeedStats:
    loaded: int = 0
    updated: int = 0
    created: int = 0
    skipped: int = 0
    errors: int = 0


def load_exercise_specs_from_dir(path: str | Path) -> Tuple[List[ExerciseSpec], List[str]]:
    base = Path(path)
    errors: List[str] = []
    specs: List[ExerciseSpec] = []
    if not base.exists():
        return [], [f"Path not found: {base}"]

    for json_path in sorted(base.rglob("*.json")):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            spec = ExerciseSpec.model_validate(data)
            specs.append(spec)
        except (json.JSONDecodeError, ValidationError, Exception) as exc:  # noqa: B902
            errors.append(f"{json_path}: {exc}")
    return specs, errors


def upsert_exercises(session: Session, specs: List[ExerciseSpec]) -> SeedStats:
    stats = SeedStats(loaded=len(specs))
    for spec in specs:
        existing = session.get(Exercise, spec.id)
        payload = {
            "id": spec.id,
            "question_text": spec.question_text,
            "type": spec.type,
            "choices": spec.choices or [],
            "correct_answer": spec.correct_answer,
            "difficulty": spec.difficulty,
            "skill_ids": spec.skill_ids or [],
            "solution_explanation": spec.solution_explanation,
            "hint": spec.hint,
            "meta": spec.metadata or {},
            "updated_at": datetime.utcnow(),
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            stats.updated += 1
        else:
            session.add(Exercise(**payload))
            stats.created += 1
    session.commit()
    return stats
