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
    due_at: datetime
    interval_days: int
    ease: float


class NextReviewOut(BaseModel):
    items: List[ReviewOut]
    remaining_today: int


class PersonaOut(BaseModel):
    user_id: UUID
    persona: str
    warmup_ts: Optional[datetime] = None


class StatsOut(BaseModel):
    user_id: UUID
    daily_due: int
    completed_today: int
    streak_days: int


class AssignABIn(BaseModel):
    user_id: UUID
    experiment: str
    bucket: str


class XPOut(BaseModel):
    user_id: UUID
    total_xp: int
    streak_days: int
    last_event: Optional[datetime] = None
