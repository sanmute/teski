from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    TESKI_SECRET_KEY: str  # no default in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12 hours
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

auth_settings = AuthSettings()


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
    EX_FLOW_DEFAULT: str = field(default_factory=lambda: _get_env("EX_FLOW_DEFAULT", "review_first"))
    INTERLEAVE_RATIO: float = field(default_factory=lambda: float(_get_env("INTERLEAVE_RATIO", "0.5")))
    DEV_MODE: bool = field(default_factory=lambda: _parse_bool(_get_env("DEV_MODE", "true")))
    EX_AGENDA_REVIEW_FIRST: bool = field(default_factory=lambda: _parse_bool(_get_env("EX_AGENDA_REVIEW_FIRST", "true")))
    SMTP_HOST: str = field(default_factory=lambda: _get_env("SMTP_HOST", "localhost"))
    SMTP_PORT: int = field(default_factory=lambda: int(_get_env("SMTP_PORT", "587")))
    SMTP_USERNAME: str = field(default_factory=lambda: _get_env("SMTP_USERNAME", ""))
    SMTP_PASSWORD: str = field(default_factory=lambda: _get_env("SMTP_PASSWORD", ""))
    SMTP_FROM: str = field(default_factory=lambda: _get_env("SMTP_FROM", "no-reply@teski.local"))
    SMTP_USE_TLS: bool = field(default_factory=lambda: _parse_bool(_get_env("SMTP_USE_TLS", "true")))

    def __post_init__(self) -> None:
        if self.EX_FLOW_DEFAULT not in {"review_first", "interleave"}:
            self.EX_FLOW_DEFAULT = "review_first"
        self.INTERLEAVE_RATIO = min(1.0, max(0.0, self.INTERLEAVE_RATIO))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
