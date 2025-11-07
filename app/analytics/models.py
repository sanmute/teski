from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from app.models import AppSQLModel


class AnalyticsDailyAgg(AppSQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_analytics_daily_user_day"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    day: date = Field(index=True)
    counts: dict[str, int] = Field(default_factory=dict, sa_type=JSON)
    sessions: int = Field(default=0, index=True)
    reviews: int = Field(default=0, index=True)
    minutes_active: float = Field(default=0.0)
    last_recomputed_at: datetime = Field(default_factory=datetime.utcnow, index=True)
