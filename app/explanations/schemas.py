from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ExplanationRequest(BaseModel):
    text: str
    topic: Optional[str] = None
    mode: Optional[str] = "auto"


class ExplanationBlock(BaseModel):
    style: str
    title: Optional[str] = None
    content: str


class ExplanationResponse(BaseModel):
    chosen_style: str
    blocks: list[ExplanationBlock]
