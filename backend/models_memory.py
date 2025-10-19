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
# <<< MEMORY END
