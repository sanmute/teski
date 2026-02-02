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


class StudyProfile(SQLModel, table=True):
    __tablename__ = "study_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Uses external_user_id (UUID string) so we don't depend on internal integer IDs.
    user_id: str = Field(index=True)
    # Arbitrary profile payload (e.g., goals, availability, weak_areas, preferences, etc.)
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
