from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from db import get_session
from models_exercise import Exercise
from services.exercise_loader import ExerciseSpec, load_exercise_specs_from_dir, upsert_exercises

router = APIRouter(prefix="/ex", tags=["exercises"])


# -------------------- Schemas -------------------- #
class ExerciseOut(BaseModel):
    id: str
    question_text: str
    type: str
    choices: List[str] = Field(default_factory=list)
    difficulty: int = 1
    skill_ids: List[str] = Field(default_factory=list)
    solution_explanation: Optional[str] = None
    hint: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correct_answer: Optional[str] = None  # included for now


class ExerciseListOut(BaseModel):
    items: List[ExerciseOut]


class GradeIn(BaseModel):
    user_id: str
    exercise_id: str
    answer: Any


class MistakeOut(BaseModel):
    family: str
    subtype: str
    label: str


class GradeOut(BaseModel):
    ok: bool
    exercise_id: str
    is_correct: bool
    correct_answer: str
    solution_explanation: Optional[str] = None
    hint: Optional[str] = None
    mistake: Optional[MistakeOut] = None
    xp_delta: int
    next_recommendation: Optional[Dict[str, Any]] = None


class SeedResult(BaseModel):
    ok: bool
    created: int
    updated: int
    loaded: int
    skipped: int
    errors: List[str] = Field(default_factory=list)
    path: str


# -------------------- Helpers -------------------- #
def _to_out(ex: Exercise, include_answer: bool = True) -> ExerciseOut:
    data = ex.to_dict(include_answer=include_answer)
    return ExerciseOut(**data)


def _require_admin(header_key: str | None) -> None:
    env_key = os.getenv("TESKI_ADMIN_KEY")
    if env_key:
        if not header_key or header_key != env_key:
            raise HTTPException(status_code=403, detail="admin key required")
    # if no env key set, allow for local/dev usage


# -------------------- Routes -------------------- #
@router.get("/list", response_model=ExerciseListOut)
def list_exercises(
    user_id: Optional[str] = Query(default=None),
    difficulty_min: int = Query(default=1, ge=1),
    difficulty_max: int = Query(default=5, ge=1),
    skill_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    stmt = select(Exercise).where(
        Exercise.difficulty >= difficulty_min,
        Exercise.difficulty <= difficulty_max,
    ).order_by(Exercise.difficulty.asc(), Exercise.id.asc())
    rows = session.exec(stmt).all()
    filtered: List[Exercise] = []
    for ex in rows:
        if skill_id and (skill_id not in (ex.skill_ids or [])):
            continue
        filtered.append(ex)
        if len(filtered) >= limit:
            break
    return ExerciseListOut(items=[_to_out(ex, include_answer=True) for ex in filtered])


@router.get("/get", response_model=ExerciseOut)
def get_exercise(id: str = Query(...), session: Session = Depends(get_session)):
    ex = session.get(Exercise, id)
    if not ex:
        raise HTTPException(status_code=404, detail="exercise_not_found")
    return _to_out(ex, include_answer=True)


@router.post("/answer", response_model=GradeOut)
def answer_exercise(payload: GradeIn, session: Session = Depends(get_session)):
    ex = session.get(Exercise, payload.exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    mistake: Optional[MistakeOut] = None
    is_correct = False

    # Multiple choice grading
    if ex.type == "multiple_choice":
        if payload.answer is None or payload.answer == "":
            mistake = MistakeOut(family="behavioral", subtype="blank", label="behavioral:blank")
        else:
            submitted = str(payload.answer)
            correct = str(ex.correct_answer)
            is_correct = submitted == correct
            if not is_correct:
                mistake = MistakeOut(family="behavioral", subtype="wrong_choice", label="behavioral:wrong_choice")
    else:
        # Placeholder for future types
        raise HTTPException(status_code=400, detail=f"unsupported exercise type: {ex.type}")

    diff = ex.difficulty or 1
    xp_delta = max(5, 10 - diff) if is_correct else 2

    return GradeOut(
        ok=True,
        exercise_id=ex.id,
        is_correct=is_correct,
        correct_answer=str(ex.correct_answer),
        solution_explanation=ex.solution_explanation,
        hint=ex.hint,
        mistake=mistake,
        xp_delta=xp_delta,
        next_recommendation=None,
    )


@router.post("/seed", response_model=SeedResult)
def seed_exercises(
    path: Optional[str] = Query(default=None, description="Directory of exercise JSON files"),
    admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
    session: Session = Depends(get_session),
):
    _require_admin(admin_key)
    content_dir = path or os.getenv("EXERCISES_DIR", "seed/exercises")
    specs, errors = load_exercise_specs_from_dir(content_dir)
    stats = upsert_exercises(session, specs)
    stats.errors = len(errors)
    return SeedResult(
        ok=errors == [],
        created=stats.created,
        updated=stats.updated,
        loaded=stats.loaded,
        skipped=stats.skipped,
        errors=errors,
        path=str(content_dir),
    )
