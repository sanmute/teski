from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import SQLModel, Field


class UserOnboarding(SQLModel, table=True):
    __tablename__ = "user_onboarding"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    answers: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    skipped: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
