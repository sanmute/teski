from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MistakeInfo:
    family: str
    subtype: str
    severity: str = "medium"
    is_near_miss: bool = False
    raw_label: Optional[str] = None

    @property
    def label(self) -> str:
        return self.raw_label or f"{self.family}:{self.subtype}"
