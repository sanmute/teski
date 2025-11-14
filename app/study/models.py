from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field

from app.models import AppSQLModel, _utcnow


class StudySession(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True, foreign_key="user.id")
    task_id: int = Field(index=True, foreign_key="learner_task.id")
    task_block_id: int = Field(index=True, foreign_key="learner_task_block.id")
    started_at: datetime = Field(default_factory=_utcnow, index=True)
    ended_at: Optional[datetime] = Field(default=None, index=True)
    planned_duration_minutes: int
    actual_duration_minutes: Optional[int] = Field(default=None)
    status: str = Field(default="active", index=True)
    goal_text: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class StudyReflection(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True, foreign_key="studysession.id")
    user_id: UUID = Field(index=True, foreign_key="user.id")
    goal_completed: Optional[bool] = Field(default=None)
    perceived_difficulty: Optional[int] = Field(default=None)
    time_feeling: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
