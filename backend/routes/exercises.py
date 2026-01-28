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
from models_analytics import AnalyticsEvent
from services.exercise_loader import ExerciseSpec, load_exercise_specs_from_dir, upsert_exercises

router = APIRouter(prefix="/ex", tags=["exercises"])


# -------------------- Schemas -------------------- #
class ExerciseOut(BaseModel):
    # Fields aligned with existing frontend expectations
    id: str
    concept: str
    type: str
    difficulty: int = 1
    tags: List[str] = Field(default_factory=list)
    prompt: str
    choices: Optional[List[Dict[str, str]]] = None
    correct_answer: Optional[str] = None  # still included for now
    solution_explanation: Optional[str] = None
    hint: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExerciseListOut(BaseModel):
    items: List[ExerciseOut]
    page: int = 1
    page_size: int
    total: int


class GradeIn(BaseModel):
    user_id: str
    exercise_id: str
    answer: Any


class MistakeOut(BaseModel):
    family: str
    subtype: str
    label: str


class GradeOut(BaseModel):
    # Backend canonical fields
    ok: bool
    exercise_id: str
    is_correct: bool
    correct_answer: str
    solution_explanation: Optional[str] = None
    hint: Optional[str] = None
    mistake: Optional[MistakeOut] = None
    xp_delta: int
    next_recommendation: Optional[Dict[str, Any]] = None
    # Legacy/front-end compatibility fields
    correct: Optional[bool] = None
    xp_awarded: Optional[int] = None
    explanation: Optional[str] = None
    persona_msg: Optional[str] = None
    persona_reaction: Optional[Dict[str, Any]] = None


class SeedResult(BaseModel):
    ok: bool
    created: int
    updated: int
    loaded: int
    skipped: int
    errors: List[str] = Field(default_factory=list)
    path: str


# -------------------- Helpers -------------------- #
def _map_type(t: str) -> str:
    t_norm = t.lower()
    if t_norm in {"mcq", "multiple_choice"}:
        return "MCQ"
    if t_norm in {"numeric"}:
        return "NUMERIC"
    if t_norm in {"short_answer", "short"}:
        return "SHORT"
    return t.upper()


def _to_out(ex: Exercise, include_answer: bool = True) -> ExerciseOut:
    choices_struct = None
    if ex.choices:
        choices_struct = [{"id": str(idx), "text": str(choice)} for idx, choice in enumerate(ex.choices)]
    tags = []
    if ex.skill_ids:
        tags = list(ex.skill_ids)
    meta = ex.meta or {}
    concept = meta.get("topic") or ex.question_text[:80]
    data = {
        "id": ex.id,
        "concept": concept,
        "type": _map_type(ex.type),
        "difficulty": int(ex.difficulty or 1),
        "tags": tags,
        "prompt": ex.question_text,
        "choices": choices_struct,
        "solution_explanation": ex.solution_explanation,
        "hint": ex.hint,
        "metadata": meta,
    }
    if include_answer:
        data["correct_answer"] = str(ex.correct_answer)
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
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    stmt = select(Exercise).where(
        Exercise.difficulty >= difficulty_min,
        Exercise.difficulty <= difficulty_max,
    ).order_by(Exercise.difficulty.asc(), Exercise.id.asc())
    rows = session.exec(stmt).all()
    filtered: List[Exercise] = []
    search_lc = (search or "").strip().lower()
    for ex in rows:
        if skill_id and (skill_id not in (ex.skill_ids or [])):
            continue
        if search_lc:
            if search_lc not in ex.question_text.lower():
                meta_topic = (ex.meta or {}).get("topic", "")
                if search_lc not in str(meta_topic).lower():
                    continue
        filtered.append(ex)
        if len(filtered) >= limit:
            break
    items = [_to_out(ex, include_answer=True) for ex in filtered]
    return ExerciseListOut(items=items, page=1, page_size=len(items), total=len(items))


@router.get("/get", response_model=ExerciseOut)
def get_exercise(id: str = Query(...), session: Session = Depends(get_session)):
    ex = session.get(Exercise, id)
    if not ex:
        raise HTTPException(status_code=404, detail="exercise_not_found")
    return _to_out(ex, include_answer=True)


@router.post("/answer", response_model=GradeOut)
@router.post("/submit", response_model=GradeOut)  # legacy alias for frontend
def answer_exercise(payload: GradeIn, session: Session = Depends(get_session)):
    ex = session.get(Exercise, payload.exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    mistake: Optional[MistakeOut] = None
    is_correct = False

    # Extract raw answer value
    raw_answer = payload.answer
    if isinstance(raw_answer, dict) and "choice" in raw_answer:
        raw_answer = raw_answer.get("choice")
    elif isinstance(raw_answer, dict) and "value" in raw_answer:
        raw_answer = raw_answer.get("value")
    elif isinstance(raw_answer, dict) and "text" in raw_answer:
        raw_answer = raw_answer.get("text")

    # Multiple choice grading
    if ex.type == "multiple_choice":
        if raw_answer is None or raw_answer == "":
            mistake = MistakeOut(family="behavioral", subtype="blank", label="behavioral:blank")
        else:
            submitted = str(raw_answer)
            correct = str(ex.correct_answer)
            is_correct = submitted == correct
            if not is_correct:
                mistake = MistakeOut(family="behavioral", subtype="wrong_choice", label="behavioral:wrong_choice")
    else:
        # Placeholder for future types
        raise HTTPException(status_code=400, detail=f"unsupported exercise type: {ex.type}")

    diff = ex.difficulty or 1
    xp_delta = max(5, 10 - diff) if is_correct else 2

    # Log analytics events
    try:
        session.add(
            AnalyticsEvent(
                user_id=payload.user_id,
                event_type="exercise_answer",
                meta={"exercise_id": ex.id, "skill_ids": ex.skill_ids, "difficulty": ex.difficulty},
            )
        )
        session.add(
            AnalyticsEvent(
                user_id=payload.user_id,
                event_type="exercise_correct" if is_correct else "exercise_incorrect",
                meta={"exercise_id": ex.id, "skill_ids": ex.skill_ids, "difficulty": ex.difficulty},
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        # don't block response on logging errors

    # Align with legacy frontend field names
    return GradeOut(
        ok=True,
        exercise_id=ex.id,
        is_correct=is_correct,
        correct_answer=str(ex.correct_answer),
        solution_explanation=ex.solution_explanation,
        hint=ex.hint,
        mistake=mistake,
        xp_delta=xp_delta,
        correct=is_correct,
        xp_awarded=xp_delta,
        explanation=ex.solution_explanation,
        persona_msg=None,
        persona_reaction=None,
        next_recommendation=None,
    )


@router.post("/seed", response_model=SeedResult)
def seed_exercises(
    path: Optional[str] = Query(default=None, description="Directory of exercise JSON files"),
    admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
    session: Session = Depends(get_session),
):
    _require_admin(admin_key)
    # Default to "seed" so JSON files placed in backend/seed are picked up in the Fly image.
    content_dir = path or os.getenv("EXERCISES_DIR", "seed")
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
