from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlmodel import Column, Field
from sqlalchemy.dialects.sqlite import JSON

from app.models import AppSQLModel


class PilotInvite(AppSQLModel, table=True):
    """Invitation codes used to onboard private pilot cohorts."""

    __tablename__ = "pilot_invites"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    email_hint: Optional[str] = Field(default=None)
    used_by_user: Optional[UUID] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    used_at: Optional[datetime] = Field(default=None, index=True)


class PilotConsent(AppSQLModel, table=True):
    """Tracks consent approvals for pilot users."""

    __tablename__ = "pilot_consents"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True, unique=True)
    accepted: bool = Field(default=False, index=True)
    text_version: str = Field(default="v1")
    accepted_at: Optional[datetime] = Field(default=None, index=True)


class PilotSession(AppSQLModel, table=True):
    """Aggregated study sessions captured during pilot programs."""

    __tablename__ = "pilot_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    invite_id: Optional[int] = Field(default=None, foreign_key="pilot_invites.id", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    ended_at: Optional[datetime] = Field(default=None, index=True)
    minutes_active: int = Field(default=0)
    topic_id: Optional[str] = Field(default=None, index=True)


class PilotFeedback(AppSQLModel, table=True):
    """Free-text pilot user feedback captured in-app."""

    __tablename__ = "pilot_feedback"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, index=True)
    message: str
    context_json: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
