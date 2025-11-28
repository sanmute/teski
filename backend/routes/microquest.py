from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.db import get_session
from backend.models import User
from backend.models_exercise import Exercise
from backend.models_microquest import MicroQuest, MicroQuestAnswer, MicroQuestExercise
from backend.routes.deps import get_current_user
from backend.schemas_microquest import (
    ExerciseDTO,
    MicroQuestAnswerRequest,
    MicroQuestAnswerResponse,
    MicroQuestCompleteResponse,
    MicroQuestGetResponse,
    MicroQuestStartRequest,
    MicroQuestStartResponse,
)

router = APIRouter(prefix="/ex/micro-quest", tags=["micro-quest"])


def _exercise_dtos(exercises: List[Exercise]) -> List[ExerciseDTO]:
    return [
        ExerciseDTO(
            id=ex.id,
            prompt=ex.prompt,
            type=ex.type,
            choices=ex.choices,
        )
        for ex in exercises
    ]


@router.post("/start", response_model=MicroQuestStartResponse)
def start_microquest(
    payload: MicroQuestStartRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    mq = MicroQuest(user_id=current_user.id)
    session.add(mq)
    session.commit()
    session.refresh(mq)

    desired = 3
    query = select(Exercise)
    if payload.skill_id:
        query = query.where(Exercise.primary_skill_id == str(payload.skill_id))
    exercises = session.exec(query.limit(desired)).all()
    if not exercises:
        raise HTTPException(status_code=400, detail="No exercises available")

    for idx, ex in enumerate(exercises):
        session.add(
            MicroQuestExercise(
                microquest_id=mq.id,
                exercise_id=ex.id,
                order_index=idx,
            )
        )
    session.commit()

    return MicroQuestStartResponse(
        microquest_id=mq.id,
        exercises=_exercise_dtos(exercises),
    )


@router.get("/{microquest_id}", response_model=MicroQuestGetResponse)
def get_microquest(
    microquest_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    mq = session.get(MicroQuest, microquest_id)
    if not mq or mq.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Micro-quest not found")

    links = session.exec(
        select(MicroQuestExercise)
        .where(MicroQuestExercise.microquest_id == mq.id)
        .order_by(MicroQuestExercise.order_index)
    ).all()
    if not links:
        raise HTTPException(status_code=400, detail="Micro-quest has no exercises")

    exercise_ids = [l.exercise_id for l in links]
    exercises = session.exec(select(Exercise).where(Exercise.id.in_(exercise_ids))).all()
    by_id = {ex.id: ex for ex in exercises}

    ordered_exercises: List[Exercise] = []
    for link in links:
        ex = by_id.get(link.exercise_id)
        if ex:
            ordered_exercises.append(ex)

    return MicroQuestGetResponse(
        microquest_id=mq.id,
        exercises=_exercise_dtos(ordered_exercises),
    )


@router.post("/{microquest_id}/answer", response_model=MicroQuestAnswerResponse)
def answer_microquest_exercise(
    microquest_id: UUID,
    payload: MicroQuestAnswerRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    mq = session.get(MicroQuest, microquest_id)
    if not mq or mq.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Micro-quest not found")
    if mq.status != "active":
        raise HTTPException(status_code=400, detail="Micro-quest is not active")

    link = session.exec(
        select(MicroQuestExercise).where(
            MicroQuestExercise.microquest_id == mq.id,
            MicroQuestExercise.exercise_id == payload.exercise_id,
        )
    ).first()
    if not link:
        raise HTTPException(status_code=400, detail="Exercise not part of this micro-quest")

    ex = session.get(Exercise, payload.exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")

    user_answer = payload.answer.strip().lower()
    correct_answer = ex.correct_answer.strip().lower()
    is_correct = user_answer == correct_answer

    session.add(
        MicroQuestAnswer(
            microquest_id=mq.id,
            exercise_id=ex.id,
            user_id=current_user.id,
            answer=payload.answer,
            correct=is_correct,
        )
    )
    link.answered = True
    session.add(link)
    session.commit()

    return MicroQuestAnswerResponse(
        correct=is_correct,
        explanation=ex.explanation or "",
    )


@router.post("/{microquest_id}/complete", response_model=MicroQuestCompleteResponse)
def complete_microquest(
    microquest_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    mq = session.get(MicroQuest, microquest_id)
    if not mq or mq.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Micro-quest not found")
    if mq.status != "active":
        raise HTTPException(status_code=400, detail="Micro-quest already completed")

    mq.status = "completed"
    mq.completed_at = datetime.utcnow()

    answers = session.exec(
        select(MicroQuestAnswer).where(MicroQuestAnswer.microquest_id == mq.id)
    ).all()
    total_count = len(answers)
    correct_count = sum(1 for a in answers if a.correct)
    accuracy = correct_count / total_count if total_count > 0 else 0.0

    session.add(mq)
    session.commit()

    try:
        from backend.services.debrief_engine import build_microquest_debrief

        debrief = build_microquest_debrief(
            user_id=current_user.id,
            microquest_id=mq.id,
            session_summary_repo=None,
            trajectory_service=None,
        )
        debrief_payload = debrief.dict() if hasattr(debrief, "dict") else debrief
    except Exception:
        if accuracy >= 0.8:
            msg = "You handled this set with a lot of control. This is a solid result."
        elif accuracy >= 0.5:
            msg = "You got about half of these right. There is structure here, but also clear room to grow."
        else:
            msg = "This run was challenging. Treat it as a map of what to focus on next, not a verdict on your potential."
        debrief_payload = {"message": msg}

    return MicroQuestCompleteResponse(
        microquest_id=mq.id,
        correct_count=correct_count,
        total_count=total_count,
        accuracy=accuracy,
        debrief=debrief_payload,
    )
