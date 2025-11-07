from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PrefsIn(BaseModel):
    user_id: UUID
    allow_llm_feedback: Optional[bool] = None
    allow_voice_stt: Optional[bool] = None
    allow_elaboration_prompts: Optional[bool] = None
    allow_concept_maps: Optional[bool] = None
    allow_transfer_checks: Optional[bool] = None
    store_self_explanations: Optional[bool] = None
    store_concept_maps: Optional[bool] = None


class PrefsOut(BaseModel):
    user_id: UUID
    allow_llm_feedback: bool
    allow_voice_stt: bool
    allow_elaboration_prompts: bool
    allow_concept_maps: bool
    allow_transfer_checks: bool
    store_self_explanations: bool
    store_concept_maps: bool
