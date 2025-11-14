from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from app.models import AppSQLModel, _utcnow


class LearnerProfile(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True, unique=True)
    approach_new_topic: Optional[str] = Field(default=None)
    stuck_strategy: Optional[str] = Field(default=None)
    explanation_style: Optional[str] = Field(default=None)
    confidence_baseline: Optional[int] = Field(default=None, ge=1, le=5)
    long_assignment_reaction: Optional[str] = Field(default=None)
    focus_time: Optional[str] = Field(default=None)
    communication_style: Optional[str] = Field(default=None)
    practice_style: Optional[str] = Field(default=None)
    time_estimation_bias: Optional[str] = Field(default=None)
    analytical_comfort: Optional[int] = Field(default=None, ge=1, le=5)
    feedback_preference: Optional[str] = Field(default=None)
    challenges: Optional[List[str]] = Field(default=None, sa_type=JSON)
    primary_device: Optional[str] = Field(default=None)
    proactivity_level: Optional[str] = Field(default=None)
    semester_goal: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
