from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class StudyPack(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)
    topic: str
    resources_json: str                 # JSON string
    practice_json: str                  # JSON string
    brief_speech: str
    cta: str
    created_at: datetime
    ttl_hours: int = 24