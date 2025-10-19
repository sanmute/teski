# >>> MEMORY START
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Literal

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlmodel import Field, SQLModel, UniqueConstraint

ErrorType = Literal["recall", "concept", "format", "spelling", "unit", "other"]
PlanStatus = Literal["pending", "served", "completed", "skipped"]


class MistakeLog(SQLModel, table=True):
    __tablename__ = "mistake_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    skill_id: Optional[int] = Field(default=None, index=True)
    template_code: Optional[str] = Field(default=None, index=True)
    instance_id: Optional[int] = Field(default=None, index=True)
    error_type: str = Field(default="other", index=True)
    # >>> MEMORY V1 START
    error_subtype: Optional[str] = Field(default=None, index=True)
    # <<< MEMORY V1 END
    detail: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SQLITE_JSON))
    weight: float = Field(default=1.0)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    resolved_at: Optional[datetime] = Field(default=None, index=True)


class ResurfacePlan(SQLModel, table=True):
    __tablename__ = "resurface_plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    skill_id: Optional[int] = Field(default=None, index=True)
    template_code: Optional[str] = Field(default=None, index=True)
    scheduled_for: datetime = Field(index=True)
    status: str = Field(default="pending", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "template_code", "scheduled_for", name="uq_user_tpl_time"),)


class MemoryStat(SQLModel, table=True):
    __tablename__ = "memory_stats"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    skill_id: Optional[int] = Field(default=None, index=True)
    mistake_count: int = Field(default=0)
    last_missed_at: Optional[datetime] = Field(default=None)
    last_mastered_at: Optional[datetime] = Field(default=None)
    stability: float = Field(default=0.3)

    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_mem_user_skill"),)
# >>> MEMORY V1 START
ErrorSubtype = Literal[
    "near_miss",
    "false_friend",
    "spelling",
    "unit",
    "sign",
    "algebra",
    "concept",
    "recall",
    "format",
    "other",
]
ReviewStatus = Literal["due", "scheduled", "served", "completed", "skipped"]


class ReviewCard(SQLModel, table=True):
    """
    Per-user review items with spaced repetition metadata.
    """

    __tablename__ = "review_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    skill_id: Optional[int] = Field(default=None, index=True)
    template_code: Optional[str] = Field(default=None, index=True)
    easiness: float = Field(default=2.3)
    stability: float = Field(default=0.3)
    last_interval_days: float = Field(default=0.0)
    next_review_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    status: str = Field(default="scheduled", index=True)
    last_result: Optional[bool] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "template_code", name="uq_review_user_tpl"),)
# <<< MEMORY V1 END
# <<< MEMORY END
