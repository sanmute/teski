from __future__ import annotations

from typing import Any, Dict, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ExplainIn(BaseModel):
    user_id: UUID
    topic_id: str
    mode: Literal["text", "voice"] = "text"
    text: str


class ExplainOut(BaseModel):
    score_deep: int
    rubric: Dict[str, Any]
    next_prompts: Dict[str, Any]


class ElaborateIn(BaseModel):
    topic: str
    user_answer: str
    language: str = "en"


class ElaborateOut(BaseModel):
    question: str
    model_answer: str
    model_config = {"protected_namespaces": ()}


class ConfidenceIn(BaseModel):
    user_id: UUID
    item_id: str
    topic_id: str
    confidence: int = Field(ge=1, le=5)
    correct: bool


class ConceptMapSaveIn(BaseModel):
    user_id: UUID
    topic_id: str
    graph_json: Dict[str, Any]


class ConceptMapOut(BaseModel):
    topic_id: str
    graph_json: Dict[str, Any]


class SettingsIn(BaseModel):
    user_id: UUID
    interleaving: bool


class SettingsOut(BaseModel):
    interleaving: bool


class HistoryOut(BaseModel):
    items: List[Dict[str, Any]]
