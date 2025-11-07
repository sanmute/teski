from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field

from app.models import AppSQLModel


class FeedbackCache(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key_hash: str = Field(index=True, unique=True)
    model_used: str
    language: str
    persona: str
    topic: Optional[str] = None
    feedback_text: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_eur: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class FeedbackEvent(AppSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    model_used: str
    tokens_in: int
    tokens_out: int
    cost_eur: float
    cached_hit: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
