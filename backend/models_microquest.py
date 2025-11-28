from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class MicroQuest(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = Field(default="active", index=True)


class MicroQuestExercise(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    microquest_id: UUID = Field(foreign_key="microquest.id", index=True)
    exercise_id: UUID = Field(foreign_key="exercise.id", index=True)
    order_index: int = Field(index=True)
    answered: bool = Field(default=False, index=True)


class MicroQuestAnswer(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    microquest_id: UUID = Field(foreign_key="microquest.id", index=True)
    exercise_id: UUID = Field(foreign_key="exercise.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    answer: str
    correct: bool
