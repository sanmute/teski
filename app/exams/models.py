from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from app.models import AppSQLModel, _utcnow


class StudyBlockKind(str, Enum):
    LEARN = "learn"
    REVIEW = "review"
    DRILL = "drill"
    MOCK = "mock"


class StudyBlockStatus(str, Enum):
    SCHEDULED = "scheduled"
    DONE = "done"
    SKIPPED = "skipped"


class Exam(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str
    course: str
    exam_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow, index=True)
    target_grade: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None)

    __table_args__ = (sa.Index("ix_exam_user_exam_at", "user_id", "exam_at"),)


class ExamTopic(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    exam_id: UUID = Field(foreign_key="exam.id", index=True)
    name: str
    est_minutes: int = Field(ge=0)
    priority: int = Field(default=2, ge=1, le=3)
    dependencies: List[str] = Field(default_factory=list, sa_type=JSON)


class StudyPlan(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    exam_id: UUID = Field(foreign_key="exam.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow, index=True)
    version: int = Field(default=1, ge=1)
    strategy: str


class StudyBlock(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    plan_id: UUID = Field(foreign_key="studyplan.id", index=True)
    exam_id: UUID = Field(foreign_key="exam.id", index=True)
    topic_id: Optional[UUID] = Field(default=None, foreign_key="examtopic.id", index=True)
    day: date = Field(index=True)
    start: Optional[time] = Field(default=None)
    minutes: int = Field(ge=5)
    kind: StudyBlockKind = Field(default=StudyBlockKind.LEARN)
    topic: str
    difficulty: int = Field(default=1, ge=1, le=3)
    status: StudyBlockStatus = Field(default=StudyBlockStatus.SCHEDULED)
    actual_minutes: Optional[int] = Field(default=None, ge=0)

    __table_args__ = (
        sa.Index("ix_studyblock_exam_day", "exam_id", "day"),
        sa.Index("ix_studyblock_plan_day", "plan_id", "day"),
    )


class QuestionnaireResult(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    exam_id: UUID = Field(foreign_key="exam.id", index=True)
    style: str
    payload: dict = Field(default_factory=dict, sa_type=JSON)
    created_at: datetime = Field(default_factory=_utcnow, index=True)
