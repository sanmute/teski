from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

FeedbackModel = Literal["mini:gpt4_1", "mini:haiku4_5", "pro:gpt4_1", "pro:sonnet3_7", "local:llama70b"]


class FeedbackGenerateIn(BaseModel):
    user_id: str
    persona: Literal["Calm", "Coach", "Encourager", "Snark"] = "Coach"
    topic: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    language: Literal["en", "fi"] = "en"
    summary_json: Dict[str, Any]
    max_sentences: int = Field(default=3, ge=1, le=6)


class FeedbackGenerateOut(BaseModel):
    feedback: str
    model_used: FeedbackModel
    cached: bool = False
    estimated_tokens_in: int
    estimated_tokens_out: int
    estimated_cost_eur: float


class FeedbackSummaryIn(BaseModel):
    user_id: str
    window_days: int = Field(default=7, ge=1, le=60)


class FeedbackSummaryOut(BaseModel):
    summary_json: Dict[str, Any]
