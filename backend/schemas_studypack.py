from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

ResourceType = Literal[
    "video",
    "notes",
    "practice",
    "article",
    "tool",
    "course",
    "reference",
    "guide",
    "source",
    "data",
    "template",
    "method",
    "gallery",
    "lesson",
    "exercise",
    "library",
]

class Resource(BaseModel):
    type: ResourceType
    title: str
    url: str
    why: str | None = None

class PracticeItem(BaseModel):
    prompt: str
    solution_url: Optional[str] = None
    topic: Optional[str] = None

class StudyPackOut(BaseModel):
    taskId: str
    topic: str
    resources: List[Resource]
    practice: List[PracticeItem]
    brief_speech: str
    cta: str
    created_at: datetime
