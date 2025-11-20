from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SkillMasteryOut(BaseModel):
    skill_id: UUID
    skill_name: str
    mastery: float
    updated_at: datetime | None = None
