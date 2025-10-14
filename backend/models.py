from __future__ import annotations
from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional, Dict, Any
from sqlalchemy import Column
from sqlalchemy.types import JSON
from datetime import datetime
from enum import Enum
from .settings import DEFAULT_TIMEZONE


# >>> LEADERBOARD START USER MODEL
class User(SQLModel, table=True):
    """Minimal user model used for leaderboard membership."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, sa_column_kwargs={"unique": True})
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(DEFAULT_TIMEZONE))


# >>> LEADERBOARD END USER MODEL

# >>> PERSONA START
class Persona(SQLModel, table=True):
    __tablename__ = "personas"
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True)
    display_name: str
    config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    __table_args__ = (UniqueConstraint("code", name="uq_persona_code"),)
# <<< PERSONA END

# Define Enums for Source, Status, and Escalation
class SourceEnum(str, Enum):
    gmail = "gmail"
    canvas = "canvas"
    mock = "mock"
    ics = "ics"  # Add 'ics' as a valid value

class StatusEnum(str, Enum):
    open = "open"
    done = "done"
    overdue = "overdue"

class EscalationEnum(str, Enum):
    calm = "calm"
    snark = "snark"
    disappointed = "disappointed"
    intervention = "intervention"

class Task(SQLModel, table=True):
    id: str = Field(primary_key=True)
    source: SourceEnum
    title: str
    course: Optional[str] = None
    link: Optional[str] = None
    due_iso: datetime = Field(default_factory=lambda: datetime.now(DEFAULT_TIMEZONE))
    status: StatusEnum = StatusEnum.open
    confidence: float = 1.0
    priority: int = 1               # 1 low, 2 medium, 3 high
    notes: Optional[str] = None
    owner_user_id: Optional[str] = Field(default=None, index=True)
    task_type: Optional[str] = Field(default=None, index=True)           # "essay", "quiz", ...
    estimated_minutes: Optional[int] = Field(default=None)               # e.g., 240
    suggested_start_utc: Optional[datetime] = Field(default=None)        # when Duey thinks you should start
    signals_json: Optional[str] = Field(default=None)  # JSON blob of signals used in estimate
    completed_at: Optional[str] = None 

class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str
    escalation: EscalationEnum
    persona: str                    # 'teacher' | 'roommate' | 'sergeant'
    created_at: datetime = Field(default_factory=lambda: datetime.now(DEFAULT_TIMEZONE))
    script_hints: Optional[str] = None
