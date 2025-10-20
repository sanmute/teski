from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, conint


class MistakeIn(BaseModel):
    user_id: UUID
    concept: str
    task_id: Optional[UUID] = None
    raw: Optional[str] = None
    context: Dict[str, object] = Field(default_factory=dict)


class ReviewIn(BaseModel):
    user_id: UUID
    memory_id: UUID
    grade: conint(ge=0, le=5)


class ReviewOut(BaseModel):
    memory_id: UUID
    concept: str
    next_due_at: datetime
    interval_days: int
    ease: float
    xp_awarded: int
    persona_msg: str


class NextReviewItem(BaseModel):
    memory_id: UUID
    concept: str
    due_at: datetime


class NextReviewOut(BaseModel):
    items: List[NextReviewItem]
    remaining_today: int


class PersonaOut(BaseModel):
    user_id: UUID
    persona: str
    warmup: bool
    copy: str
    warmup_ts: Optional[datetime] = None


class StatsOut(BaseModel):
    user_id: UUID
    today_reviewed: int
    daily_cap: int
    streak_days: int
    due_count: int
    exercises_correct_today: int
    exercises_incorrect_today: int
    suggested_new_exercises: int


class AssignABIn(BaseModel):
    user_id: UUID
    experiment: str


class MistakeOut(BaseModel):
    memory_id: UUID
    concept: str
    subtype: str


class XPOut(BaseModel):
    user_id: UUID
    total_xp: int
    streak_days: int
    last_event: Optional[datetime] = None
