from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str
    course: Optional[str] = None
    kind: Optional[str] = None
    due_at: Optional[datetime] = None
    base_estimated_minutes: int = Field(gt=0)


class TaskBlockRead(BaseModel):
    id: int
    task_id: int
    user_id: UUID
    start_at: Optional[datetime]
    duration_minutes: int
    label: str
    created_at: datetime


class TaskRead(BaseModel):
    id: int
    user_id: UUID
    title: str
    course: Optional[str]
    kind: Optional[str]
    due_at: Optional[datetime]
    status: str
    base_estimated_minutes: int
    personalized_estimated_minutes: int
    created_at: datetime
    updated_at: datetime
    blocks: List[TaskBlockRead] = Field(default_factory=list)


class TaskStatusUpdate(BaseModel):
    status: Literal["pending", "done"]
