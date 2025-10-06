# >>> DFE START
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

TaskType = Literal["numeric", "multiple_choice", "short_text"]


class SkillNodeCreate(BaseModel):
    key: str = Field(..., description="Canonical skill identifier")
    title: str = Field(..., description="Human readable name")
    graph_version: str = Field(default="v1")


class TaskTemplateCreate(BaseModel):
    code: str
    title: str
    skill_key: str
    graph_version: str = "v1"
    task_type: TaskType = "numeric"
    text_template: str
    parameters: Dict[str, Any]
    constraints: Optional[Dict[str, Any]] = None
    answer_spec: Dict[str, Any]


class TaskInstanceOut(BaseModel):
    instance_id: int
    template_code: str
    text: str
    params: Dict[str, Any]
    task_type: TaskType


class SubmitAnswer(BaseModel):
    answer: Any
    latency_ms: Optional[int] = Field(default=None, ge=0)


class AttemptResult(BaseModel):
    correct: bool
    mastery_after: float
# <<< DFE END
