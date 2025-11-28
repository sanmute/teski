from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel


class MicroQuestStartRequest(SQLModel):
    skill_id: Optional[UUID] = None


class ExerciseDTO(SQLModel):
    id: UUID
    prompt: str
    type: str
    choices: Optional[List[str]] = None


class MicroQuestStartResponse(SQLModel):
    microquest_id: UUID
    exercises: List[ExerciseDTO]


class MicroQuestGetResponse(SQLModel):
    microquest_id: UUID
    exercises: List[ExerciseDTO]


class MicroQuestAnswerRequest(SQLModel):
    exercise_id: UUID
    answer: str


class MicroQuestAnswerResponse(SQLModel):
    correct: bool
    explanation: str


class MicroQuestCompleteResponse(SQLModel):
    microquest_id: UUID
    correct_count: int
    total_count: int
    accuracy: float
    debrief: dict
