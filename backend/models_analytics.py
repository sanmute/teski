from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class AnalyticsEvent(SQLModel, table=True):
    """Lightweight event log for per-user activity stats."""

    __tablename__ = "analytics_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    event_type: str = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    meta: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
