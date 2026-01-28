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
        allowed = {"multiple_choice", "short_answer", "numeric"}
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
        name_lc = json_path.name.lower()
        if name_lc.startswith("tasks"):
            # ignore planner/task seed files
            continue
        raw = json_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        raw = raw.replace("}\n{", "}\n\n{")
        try:
            parsed = json.loads(raw)
            parsed_list = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            parsed_list = []
            # Try combining multiple objects into an array
            combined = "[" + raw.replace("}\r\n\r\n{", "},{").replace("}\n\n{", "},{") + "]"
            try:
                parsed = json.loads(combined)
                parsed_list = parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                pass
            # Fallback for files containing multiple JSON objects separated by blank lines
            chunks = [c.strip() for c in raw.split("\n\n") if c.strip()]
            try:
                for chunk in chunks:
                    chunk_stripped = chunk.strip()
                    if not (chunk_stripped.startswith("{") and chunk_stripped.endswith("}")):
                        # skip non-JSON chunks such as headers/markdown
                        continue
                    try:
                        parsed_list.append(json.loads(chunk_stripped))
                    except Exception:
                        # Last-resort sanitizer: escape inner quotes in string values
                        fixed_lines = []
                        for line in chunk_stripped.splitlines():
                            if '": "' in line:
                                key, val = line.split('": "', 1)
                                # keep trailing comma if present
                                trailing_comma = "," if val.rstrip().endswith(",") else ""
                                val_body = val.rstrip().rstrip(",")
                                if val_body.endswith('"'):
                                    val_body = val_body[:-1]
                                val_body_escaped = val_body.replace('"', '\\"')
                                line = f'{key}": "{val_body_escaped}"{trailing_comma}'
                            fixed_lines.append(line)
                        fixed_chunk = "\n".join(fixed_lines)
                        parsed_list.append(json.loads(fixed_chunk))
            except Exception as exc:  # pragma: no cover
                errors.append(f"{json_path}: {exc}")
                continue
        for obj in parsed_list:
            try:
                spec = ExerciseSpec.model_validate(obj)
                specs.append(spec)
            except ValidationError as exc:
                errors.append(f"{json_path}: {exc}")
            except Exception as exc:  # noqa: B902
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
