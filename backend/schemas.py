from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, Dict
from datetime import datetime

Source = Literal["gmail", "canvas", "mock", "ics"]
Status = Literal["open", "done", "overdue"]
Escalation = Literal["calm", "snark", "disappointed", "intervention"]

class TaskIn(BaseModel):
    id: str
    source: Source
    title: str
    course: Optional[str] = None
    link: Optional[str] = None
    due_iso: datetime
    status: Status = "open"
    confidence: float = 1.0
    notes: Optional[str] = None

class TaskOut(TaskIn):
    priority: int
    task_type: Optional[str] = None
    estimated_minutes: Optional[int] = None
    suggested_start_utc: Optional[datetime] = None
    link: Optional[str] = None
    completed_at: Optional[datetime] = None
    signals: Optional[Dict[str, Any]] = None

class MockLoadResp(BaseModel):
    loaded: int

class NextReminderReq(BaseModel):
    persona: Literal["teacher", "roommate", "sergeant"] = "teacher"

class NextReminderOut(BaseModel):
    taskId: str
    escalation: Escalation
    persona: str
    scriptHints: str
    due_iso: datetime
    title: str
    priority: int
