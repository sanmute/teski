from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class UserPrefs(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True, unique=True)
    allow_llm_feedback: bool = Field(default=False)
    allow_voice_stt: bool = Field(default=False)
    allow_elaboration_prompts: bool = Field(default=False)
    allow_concept_maps: bool = Field(default=False)
    allow_transfer_checks: bool = Field(default=False)
    store_self_explanations: bool = Field(default=False)
    store_concept_maps: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
