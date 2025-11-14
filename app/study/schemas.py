from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SessionPhaseStep(BaseModel):
    id: str
    label: str
    description: Optional[str] = None


class SessionPlan(BaseModel):
    phase: str
    title: str
    steps: list[SessionPhaseStep]


class StudySessionCreateRequest(BaseModel):
    task_block_id: int
    goal_text: Optional[str] = None


class StudySessionStartResponse(BaseModel):
    session_id: int
    task_id: int
    task_block_id: int
    block_label: str
    block_duration_minutes: int
    task_title: str
    course: Optional[str] = None
    kind: Optional[str] = None
    planned_duration_minutes: int
    plan_prepare: SessionPlan
    plan_focus: SessionPlan
    plan_close: SessionPlan


class StudySessionDetailResponse(StudySessionStartResponse):
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None


class StudySessionCompleteRequest(BaseModel):
    goal_completed: Optional[bool] = None
    perceived_difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    time_feeling: Optional[str] = Field(default=None)
    notes: Optional[str] = None
    actual_duration_minutes: Optional[int] = Field(default=None, ge=1)


class StudySessionCompleteResponse(BaseModel):
    session_id: int
    status: str
