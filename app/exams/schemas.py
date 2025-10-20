from __future__ import annotations

from datetime import date, datetime, time
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.exams.models import StudyBlockKind, StudyBlockStatus


class ExamIn(BaseModel):
    user_id: UUID
    title: str
    course: str
    exam_at: datetime
    target_grade: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None


class TopicIn(BaseModel):
    name: str
    est_minutes: int = Field(ge=0)
    priority: Optional[int] = Field(default=2, ge=1, le=3)
    dependencies: Optional[List[str]] = Field(default=None)

    @field_validator("dependencies", mode="before")
    @classmethod
    def _default_dependencies(cls, value: Optional[List[str]]) -> List[str]:
        return list(value or [])


class PlannerOptions(BaseModel):
    buffer_days: int = Field(default=2, ge=0)
    daily_cap_min: int = Field(default=120, ge=30)
    min_block: int = Field(default=25, ge=15)
    mock_count: int = Field(default=2, ge=0)
    interleave_ratio: float = Field(default=0.5, ge=0.0, le=1.0)


class ExamOut(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    course: str
    exam_at: datetime
    created_at: datetime
    target_grade: Optional[int]
    notes: Optional[str]


class TopicOut(BaseModel):
    id: UUID
    exam_id: UUID
    name: str
    est_minutes: int
    priority: int
    dependencies: List[str]


class BlockOut(BaseModel):
    id: UUID
    plan_id: UUID
    exam_id: UUID
    topic_id: Optional[UUID] = None
    day: date
    start: Optional[time]
    minutes: int
    kind: StudyBlockKind
    topic: str
    difficulty: int
    status: StudyBlockStatus
    actual_minutes: Optional[int] = None


class PlanOut(BaseModel):
    id: UUID
    exam_id: UUID
    created_at: datetime
    version: int
    strategy: str
    blocks: List[BlockOut]


class QuestionnaireIn(BaseModel):
    style: str
    answers: Dict[str, int]


class QuestionnaireOut(BaseModel):
    style: str
    weights: Dict[str, float]


class PlanProgressIn(BaseModel):
    block_id: UUID
    status: StudyBlockStatus
    minutes_spent: Optional[int] = Field(default=None, ge=0)


class AgendaItem(BaseModel):
    kind: str
    block_id: Optional[UUID] = None
    topic: Optional[str] = None
    minutes: Optional[int] = None
    status: Optional[StudyBlockStatus] = None
    type: Optional[str] = Field(default=None, description="Alias for block kind when applicable.")
    memory_id: Optional[UUID] = None
    concept: Optional[str] = None
    due_at: Optional[datetime] = None
