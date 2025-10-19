# >>> MEMORY START
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

ErrorType = Literal["recall", "concept", "format", "spelling", "unit", "other"]
PhaseType = Literal["preTask", "duringTask", "postTaskSuccess", "postTaskFail"]


class LogMistakeIn(BaseModel):
    instance_id: Optional[int] = None
    template_code: Optional[str] = None
    skill_id: Optional[int] = None
    error_type: ErrorType = "other"
    detail: Dict[str, Any] = {}


class PlanBuildIn(BaseModel):
    count: int = 3
    horizon_minutes: int = 1440


class NextTasksOut(BaseModel):
    items: List[Dict[str, Any]]
# >>> MEMORY V1 START
ErrorSubtype = Literal[
    "near_miss",
    "false_friend",
    "spelling",
    "unit",
    "sign",
    "algebra",
    "concept",
    "recall",
    "format",
    "other",
]


class LogMistakeInV1(BaseModel):
    instance_id: Optional[int] = None
    template_code: Optional[str] = None
    skill_id: Optional[int] = None
    error_type: Optional[str] = "other"
    error_subtype: Optional[ErrorSubtype] = None
    detail: Dict[str, Any] = {}


class BuildReviewsIn(BaseModel):
    max_new: int = 3
    horizon_minutes: int = 1440


class ReviewItemOut(BaseModel):
    type: Literal["review"]
    review_card_id: int
    template_code: Optional[str]
    instance_id: Optional[int] = None
    prompt: Optional[str] = None


class WarmupOut(BaseModel):
    items: List[ReviewItemOut]
# <<< MEMORY V1 END
# <<< MEMORY END
