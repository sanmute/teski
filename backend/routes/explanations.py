from __future__ import annotations

from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, select

from db import get_session
from models_exercise import Exercise

router = APIRouter(prefix="/api/explanations", tags=["explanations"])


class ExplanationRequest(SQLModel):
    exercise_id: str
    user_answer: Optional[Union[str, int]] = None


class ExplanationResponse(SQLModel):
    correct: bool
    explanation: str
    hint: Optional[str] = None


@router.post("/generate", response_model=ExplanationResponse)
def generate_explanation(payload: ExplanationRequest, session: Session = Depends(get_session)):
    exercise = session.exec(select(Exercise).where(Exercise.id == payload.exercise_id)).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise not found: {payload.exercise_id}",
        )

    user_ans = "" if payload.user_answer is None else str(payload.user_answer).strip()
    correct_ans = "" if exercise.correct_answer is None else str(exercise.correct_answer).strip()
    is_correct = bool(user_ans) and user_ans == correct_ans

    explanation_text = exercise.solution_explanation or "No explanation available."

    return ExplanationResponse(
        correct=is_correct,
        explanation=explanation_text,
        hint=exercise.hint,
    )
