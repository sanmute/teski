from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import SQLModel, Field


class FeedbackItem(SQLModel, table=True):
    __tablename__ = "feedback_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, index=True)
    user_email: Optional[str] = Field(default=None, index=True)
    kind: str = Field(default="feedback", index=True)  # feedback | bug | idea
    message: str
    severity: Optional[str] = Field(default=None, index=True)  # low | medium | high
    page_url: Optional[str] = None
    user_agent: Optional[str] = None
    app_version: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON))
    raffle_opt_in: bool = Field(default=False, index=True)
    raffle_name: Optional[str] = None
    raffle_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
