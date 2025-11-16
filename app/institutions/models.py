from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from app.models import AppSQLModel, _utcnow


class Institution(AppSQLModel, table=True):
    __tablename__ = "institution"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    domain: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    report_recipients: list[str] = Field(default_factory=list, sa_column=Column(JSON, default=list))

    __table_args__ = (UniqueConstraint("domain", name="uq_institution_domain"),)
