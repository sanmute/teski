# app/backend/models_integrations.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MoodleFeed(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)          # however you track users; stub "demo" if none
    ics_url: str
    added_at: datetime
    last_fetch_at: Optional[datetime] = None
    active: bool = True