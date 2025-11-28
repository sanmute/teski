from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Exercise(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    prompt: str
    type: str = Field(index=True)
    choices: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    correct_answer: str
    explanation: Optional[str] = None
    skill_ids: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    primary_skill_id: Optional[str] = Field(default=None, index=True)
    difficulty: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
