from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_list(value: str) -> List[str]:
    value = value.strip()
    if not value:
        return []
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    DATABASE_URL: str = field(default_factory=lambda: _get_env("DATABASE_URL", "sqlite:///./teski_v2.db"))
    DAILY_REVIEW_CAP: int = field(default_factory=lambda: int(_get_env("DAILY_REVIEW_CAP", "60")))
    KILL_SWITCH: bool = field(default_factory=lambda: _parse_bool(_get_env("KILL_SWITCH", "false")))
    AB_BUCKETS: List[str] = field(default_factory=lambda: _parse_list(_get_env("AB_BUCKETS", "")) or ["control", "variant_a"])
    PERSONA_DEFAULT: str = field(default_factory=lambda: _get_env("PERSONA_DEFAULT", "Calm"))
    XP_BASE: int = field(default_factory=lambda: int(_get_env("XP_BASE", "10")))
    XP_MASTERY_BONUS: int = field(default_factory=lambda: int(_get_env("XP_MASTERY_BONUS", "50")))
    NEMESIS_RECOVERY_THRESHOLD: int = field(default_factory=lambda: int(_get_env("NEMESIS_RECOVERY_THRESHOLD", "3")))
    SRS_LEEWAY_MIN: int = field(default_factory=lambda: int(_get_env("SRS_LEEWAY_MIN", "10")))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
