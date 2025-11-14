from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationPreview(BaseModel):
    message: str
    task_id: Optional[int] = None
    suggested_time: Optional[datetime] = None


class NotificationPreferenceIn(BaseModel):
    enable_task_reminders: bool = True
    enable_review_reminders: bool = True
    quiet_hours_start: Optional[int] = Field(default=None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(default=None, ge=0, le=23)
    max_per_day: int = Field(default=3, ge=1, le=10)


class NotificationPreferenceOut(NotificationPreferenceIn):
    id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime
