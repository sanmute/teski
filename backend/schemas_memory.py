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
# <<< MEMORY END
