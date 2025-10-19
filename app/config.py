from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./teski.db",
        env="DATABASE_URL",
    )
    DAILY_REVIEW_CAP: int = Field(default=60, env="DAILY_REVIEW_CAP")
    KILL_SWITCH: bool = Field(default=False, env="KILL_SWITCH")
    AB_BUCKETS: List[str] = Field(
        default_factory=lambda: ["control", "variant_a"],
        env="AB_BUCKETS",
    )
    PERSONA_DEFAULT: str = Field(default="Calm", env="PERSONA_DEFAULT")
    XP_BASE: int = Field(default=10, env="XP_BASE")
    XP_MASTERY_BONUS: int = Field(default=50, env="XP_MASTERY_BONUS")
    NEMESIS_RECOVERY_THRESHOLD: int = Field(
        default=3,
        env="NEMESIS_RECOVERY_THRESHOLD",
    )
    SRS_LEEWAY_MIN: int = Field(default=10, env="SRS_LEEWAY_MIN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
