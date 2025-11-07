from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field

from app.models import AppSQLModel


class SelfExplanation(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    topic_id: str = Field(index=True)
    mode: str = Field(default="text", index=True)
    transcript: str
    rubric: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    score_deep: int = 0
    next_prompts: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class ConfidenceLog(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    item_id: str = Field(index=True)
    topic_id: str = Field(index=True)
    confidence: int = Field(default=3, ge=1, le=5)
    correct: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class ConceptMap(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    topic_id: str = Field(index=True)
    graph_json: Dict[str, Any] = Field(
        sa_column=Column(JSON), default_factory=lambda: {"nodes": [], "edges": []}
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class ReviewSettings(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True, unique=True)
    interleaving: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
