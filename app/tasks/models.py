from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field

from app.models import AppSQLModel, _utcnow


class Task(AppSQLModel, table=True):
    __tablename__ = "learner_task"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str
    course: Optional[str] = Field(default=None)
    kind: Optional[str] = Field(default=None)
    due_at: Optional[datetime] = Field(default=None, index=True)
    base_estimated_minutes: int = Field(gt=0)
    status: str = Field(default="pending", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class TaskBlock(AppSQLModel, table=True):
    __tablename__ = "learner_task_block"
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="learner_task.id", index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    start_at: Optional[datetime] = Field(default=None)
    duration_minutes: int = Field(gt=0)
    label: str
    created_at: datetime = Field(default_factory=_utcnow)
