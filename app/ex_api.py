from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Deque, Dict, List, Optional, Tuple
from uuid import UUID

import random

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlmodel import Session, select

from app.analytics import log as log_event
from app.config import get_settings
from app.db import get_session
from app.detectors import classify_mistake
from app.exercises import Exercise, grade, load_exercises
from app.models import AnalyticsEvent, Mistake, MistakeSubtype, User
from app.personas import get_persona_copy
from app.scheduler import get_next_reviews, schedule_from_mistake
from app.timeutil import user_day_bounds
from app.xp import award as award_xp
from app.data.mock_exercises import MOCK_EXERCISES


class ExerciseListItem(BaseModel):
    id: str
    concept: str
    course: Optional[str] = None
    type: str
    difficulty: int = 1


class ExerciseListResponse(BaseModel):
    items: List[ExerciseListItem]
    page: int
    page_size: int
    total: int


class ExerciseGetOut(BaseModel):
    id: str
    type: str
    concept: str
    question: str
    difficulty: int = 1
    course: Optional[str] = None
    choices: Optional[List[str]] = None
    unit_hint: Optional[str] = None
    prompt: Optional[str] = None
    max_xp: Optional[int] = None
    hint: Optional[str] = None
    tags: Optional[List[str]] = None


class ExerciseSubmitOut(BaseModel):
    correct: bool
    info: Dict[str, Any] = Field(default_factory=dict)
    next_hint: Optional[str] = None
    persona_msg: Optional[str] = None


class NextMixedItem(BaseModel):
    kind: str
    memory_id: Optional[UUID] = None
    due_at: Optional[datetime] = None
    concept: Optional[str] = None
    exercise_id: Optional[str] = None
    preview: Optional[str] = None


class NextMixedResponse(BaseModel):
    items: List[NextMixedItem]


router = APIRouter(prefix="/ex", tags=["exercises"])

_RATE_LIMIT_WINDOW = timedelta(minutes=1)
_RATE_LIMIT_MAX = 30
_rate_limit_state: Dict[UUID, Deque[datetime]] = defaultdict(deque)


@lru_cache()
def _exercise_index() -> Dict[str, Exercise]:
    return {exercise.id: exercise for exercise in load_exercises()}


def _list_exercises() -> List[Exercise]:
    return list(_exercise_index().values())


def _get_exercise(exercise_id: str) -> Exercise:
    try:
        return _exercise_index()[exercise_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="exercise_not_found") from exc


def _ensure_user(session: Session, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user:
        return user
    user = User(id=user_id)
    session.add(user)
    session.flush()
    return user


def _reset_rate_limit() -> None:
    _rate_limit_state.clear()


def _enforce_rate_limit(user_id: UUID) -> None:
    settings = get_settings()
    if not settings.DEV_MODE:
        return

    now = datetime.utcnow()
    window_start = now - _RATE_LIMIT_WINDOW
    bucket = _rate_limit_state[user_id]
    while bucket and bucket[0] <= window_start:
        bucket.popleft()
    if len(bucket) >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")
    bucket.append(now)


def _validate_payload(exercise: Exercise, payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail={"error": "invalid_payload", "reason": "payload_must_be_object"})

    if exercise.type == "mcq":
        choice = payload.get("choice")
        if not isinstance(choice, int):
            raise HTTPException(status_code=422, detail={"error": "invalid_payload", "reason": "mcq_choice_required"})
    elif exercise.type == "numeric":
        if "value" not in payload:
            raise HTTPException(status_code=422, detail={"error": "invalid_payload", "reason": "numeric_value_required"})
        try:
            float(payload["value"])
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=422, detail={"error": "invalid_payload", "reason": "numeric_value_must_be_number"}
            )
        unit = payload.get("unit")
        if unit is not None and not isinstance(unit, str):
            raise HTTPException(
                status_code=422, detail={"error": "invalid_payload", "reason": "numeric_unit_must_be_string"}
            )
    elif exercise.type == "short_answer":
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise HTTPException(
                status_code=422, detail={"error": "invalid_payload", "reason": "short_answer_text_required"}
            )
    else:
        raise HTTPException(status_code=400, detail="unsupported_exercise_type")


@router.get("/list", response_model=ExerciseListResponse)
def list_exercises(
    course: Optional[str] = Query(default=None),
    concept: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> ExerciseListResponse:
    exercises = _list_exercises()
    if course:
        exercises = [ex for ex in exercises if ex.course == course]
    if concept:
        exercises = [ex for ex in exercises if ex.concept == concept]
    if type:
        normalized_type = type.lower()
        exercises = [ex for ex in exercises if ex.type.lower() == normalized_type]

    total = len(exercises)
    start = (page - 1) * page_size
    end = start + page_size
    items = [
        ExerciseListItem(
            id=ex.id,
            concept=ex.concept,
            course=ex.course,
            type=ex.type.upper(),
            difficulty=ex.difficulty,
        )
        for ex in exercises[start:end]
    ]
    mock_filtered = [
        mock
        for mock in MOCK_EXERCISES
        if (not type or mock["type"].lower() == type.lower()) and (not concept or mock["concept"] == concept)
    ]
    total += len(mock_filtered)
    items.extend(
        [
            ExerciseListItem(
                id=mock["id"],
                concept=mock["concept"],
                course=None,
                type=mock["type"],
                difficulty=mock["difficulty"],
            )
            for mock in mock_filtered
        ]
    )
    return ExerciseListResponse(items=items, page=page, page_size=page_size, total=total)


@router.get("/get", response_model=ExerciseGetOut)
def get_exercise(
    exercise_id: str = Query(..., alias="id"),
    session: Session = Depends(get_session),
    user_id: Optional[UUID] = Query(default=None),
) -> ExerciseGetOut:
    mock = next((item for item in MOCK_EXERCISES if item["id"] == exercise_id), None)
    if mock:
        return ExerciseGetOut(
            id=mock["id"],
            type=mock["type"],
            concept=mock["concept"],
            question=mock["prompt"],
            difficulty=mock["difficulty"],
            choices=[choice["text"] for choice in mock.get("choices", [])] if mock.get("choices") else None,
            unit_hint=mock.get("unit_hint"),
            prompt=mock["prompt"],
            max_xp=mock["max_xp"],
            hint=mock.get("hint"),
            tags=mock.get("tags"),
        )

    exercise = _get_exercise(exercise_id)

    response = ExerciseGetOut(
        id=exercise.id,
        type=exercise.type.upper(),
        concept=exercise.concept,
        question=exercise.question,
        difficulty=exercise.difficulty,
        course=exercise.course,
        prompt=exercise.meta.get("prompt") or exercise.question,
        max_xp=int(exercise.meta.get("max_xp", 10)),
        hint=exercise.meta.get("hint"),
        tags=exercise.keywords or None,
    )

    if exercise.type == "mcq":
        choices = exercise.meta.get("choices") or []
        response.choices = [str(choice.get("text", "")) for choice in choices]
    elif exercise.type == "numeric":
        answer_meta = exercise.meta.get("answer") or {}
        response.unit_hint = answer_meta.get("unit")

    log_event("exercise_shown", {"exercise_id": exercise.id}, user_id)
    return response


@router.post("/submit", response_model=ExerciseSubmitOut)
def submit_exercise(
    *,
    exercise_id: str = Query(..., alias="id"),
    user_id: UUID = Query(...),
    payload: Dict[str, Any] = Body(...),
    session: Session = Depends(get_session),
) -> ExerciseSubmitOut:
    _enforce_rate_limit(user_id)
    exercise = _get_exercise(exercise_id)
    _validate_payload(exercise, payload)
    user = _ensure_user(session, user_id)
    correct_today, incorrect_today = _today_exercise_counts(session, user)

    correct, info = grade(payload, exercise)

    if correct:
        award_xp(user, reason="exercise_correct", session=session)
        log_event("exercise_correct", {"exercise_id": exercise.id}, user_id)
        persona_msg = _persona_line(user, session, warm=correct_today == 0 and incorrect_today == 0)
        session.commit()
        return ExerciseSubmitOut(correct=True, info=info, persona_msg=persona_msg)

    # Incorrect path
    log_event("exercise_incorrect", {"exercise_id": exercise.id}, user_id)

    mistake = Mistake(
        user_id=user.id,
        concept=exercise.concept,
        raw=json.dumps(payload, default=str),
        subtype=MistakeSubtype.CONCEPTUAL,
    )
    session.add(mistake)

    schedule_from_mistake(session, user=user, concept=exercise.concept)

    expected = exercise.meta.get("answer") or {}
    relative_error = _relative_error(info.get("delta"), info.get("expected"))
    classified = classify_mistake(
        exercise.question,
        json.dumps(payload, default=str),
        json.dumps(expected, default=str),
        {
            "keywords": exercise.keywords,
            "unit_expected": info.get("unit_expected"),
            "unit_received": info.get("unit_received"),
            "unit_mismatch": info.get("unit_mismatch"),
            "relative_error": relative_error,
            "expected_value": info.get("expected"),
        },
    )
    info.setdefault("classified_as", classified)

    next_hint = None
    explanation = exercise.meta.get("explanation")
    if explanation:
        next_hint = str(explanation).split(".", 1)[0].strip()

    persona_msg = _persona_line(user, session, warm=correct_today == 0 and incorrect_today == 0)
    session.commit()
    return ExerciseSubmitOut(correct=False, info=info, next_hint=next_hint, persona_msg=persona_msg)


@router.get("/next", response_model=NextMixedResponse)
def next_items(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    course: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> NextMixedResponse:
    user = _ensure_user(session, user_id)
    settings = get_settings()
    flow = settings.EX_FLOW_DEFAULT
    exercises = _list_exercises()
    if course:
        exercises = [ex for ex in exercises if ex.course == course]

    review_items = get_next_reviews(session, user=user, limit=limit if flow == "review_first" else limit)
    remaining = limit
    mixed: List[NextMixedItem] = []

    if flow == "review_first":
        for mem in review_items:
            mixed.append(_review_item(mem))
        remaining = max(0, limit - len(review_items))
        if remaining > 0:
            mixed.extend(_exercise_items(exercises, remaining))
    else:  # interleave
        review_target = int(round(limit * settings.INTERLEAVE_RATIO))
        review_selected = review_items[:review_target]
        exercise_slots = limit - len(review_selected)

        review_iter = iter(review_selected)
        exercise_iter = iter(_exercise_items(exercises, exercise_slots))
        for _ in range(limit):
            try:
                mixed.append(next(review_iter))
            except StopIteration:
                break
            try:
                mixed.append(next(exercise_iter))
            except StopIteration:
                continue
        # append remaining exercises if slots left
        mixed.extend(list(exercise_iter))
        # if still space fill with additional reviews
        if len(mixed) < limit:
            extra_reviews = review_items[len(review_selected) :]
            for mem in extra_reviews:
                mixed.append(_review_item(mem))
                if len(mixed) >= limit:
                    break

    return NextMixedResponse(items=mixed[:limit])


def _review_item(memory) -> NextMixedItem:
    return NextMixedItem(
        kind="review",
        memory_id=memory.id,
        concept=memory.concept,
        due_at=memory.due_at,
    )


def _exercise_items(exercises: List[Exercise], count: int) -> List[NextMixedItem]:
    if count <= 0:
        return []
    pool = exercises.copy()
    random.shuffle(pool)
    selected = pool[:count]
    items: List[NextMixedItem] = []
    for ex in selected:
        preview = ex.question.splitlines()[0][:120]
        items.append(
            NextMixedItem(
                kind="exercise",
                exercise_id=ex.id,
                concept=ex.concept,
                preview=preview,
            )
        )
    return items


def _today_exercise_counts(session: Session, user: User) -> Tuple[int, int]:
    start, end = user_day_bounds(user.timezone)
    correct = session.exec(
        select(func.count()).where(
            AnalyticsEvent.user_id == user.id,
            AnalyticsEvent.kind == "exercise_correct",
            AnalyticsEvent.ts >= start,
            AnalyticsEvent.ts < end,
        )
    ).one()
    incorrect = session.exec(
        select(func.count()).where(
            AnalyticsEvent.user_id == user.id,
            AnalyticsEvent.kind == "exercise_incorrect",
            AnalyticsEvent.ts >= start,
            AnalyticsEvent.ts < end,
        )
    ).one()
    if isinstance(correct, tuple):
        correct = correct[0]
    if isinstance(incorrect, tuple):
        incorrect = incorrect[0]
    return int(correct or 0), int(incorrect or 0)


def _persona_line(user: User, session: Session, warm: bool) -> str:
    persona = user.persona or get_settings().PERSONA_DEFAULT
    line = get_persona_copy(persona, {"warmup": warm, "user_id": str(user.id)})
    return f"{persona} {line}"


def _relative_error(delta: Any, expected: Any) -> Optional[float]:
    try:
        delta = float(delta)
        expected = float(expected)
        baseline = abs(expected) if expected != 0 else 1.0
        return abs(delta) / baseline
    except (TypeError, ValueError):
        return None
