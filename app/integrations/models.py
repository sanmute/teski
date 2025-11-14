from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field

from app.models import AppSQLModel, _utcnow


class MoodleFeed(AppSQLModel, table=True):
    __tablename__ = "moodle_feed"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    ics_url: str
    added_at: datetime = Field(default_factory=_utcnow)
    last_fetch_at: Optional[datetime] = Field(default=None)
    active: bool = Field(default=True, index=True)


class MoodleFeedItem(AppSQLModel, table=True):
    __tablename__ = "moodle_feed_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    feed_id: int = Field(foreign_key="moodle_feed.id", index=True)
    external_id: str = Field(index=True)
    task_id: Optional[int] = Field(default=None, foreign_key="learner_task.id", index=True)
    title: str
    due_at: datetime
    last_synced_at: datetime = Field(default_factory=_utcnow)
