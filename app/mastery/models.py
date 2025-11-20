from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models import AppSQLModel, _utcnow


class Skill(AppSQLModel, table=True):
    __tablename__ = "skill"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True, unique=True)
    slug: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=_utcnow)


class UserSkillMastery(AppSQLModel, table=True):
    __tablename__ = "user_skill_mastery"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    skill_id: UUID = Field(foreign_key="skill.id", index=True)
    mastery: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=_utcnow)

    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill_mastery"),)
