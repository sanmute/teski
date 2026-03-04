from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator, model_validator

_ALLOWED_TYPES = {"mcq", "numeric", "short_answer"}
_ALLOWED_AB_VARIANTS = {"topic_only", "seed_based"}


class GenerateRequest(BaseModel):
    topic: str
    exercise_type: str
    difficulty: int
    count: int
    course: str | None = None
    domain: str | None = None
    seed_text: str | None = None
    language: str = "en"
    ab_variant: str | None = None

    @field_validator("exercise_type")
    @classmethod
    def validate_exercise_type(cls, v: str) -> str:
        if v not in _ALLOWED_TYPES:
            raise ValueError(f"exercise_type must be one of {sorted(_ALLOWED_TYPES)}")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("difficulty must be between 1 and 5")
        return v

    @field_validator("count")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if not (1 <= v <= 10):
            raise ValueError("count must be between 1 and 10")
        return v

    @field_validator("ab_variant")
    @classmethod
    def validate_ab_variant(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_AB_VARIANTS:
            raise ValueError(f"ab_variant must be one of {sorted(_ALLOWED_AB_VARIANTS)}")
        return v

    @model_validator(mode="after")
    def seed_text_required_for_seed_based(self) -> GenerateRequest:
        if self.ab_variant == "seed_based" and not self.seed_text:
            raise ValueError("seed_text is required when ab_variant is 'seed_based'")
        return self


class GeneratedExercise(BaseModel):
    id: str
    concept: str
    type: str
    question: str
    difficulty: int
    skill_ids: list[str]
    keywords: list[str]
    course: str | None = None
    domain: str | None = None
    subdomain: str | None = None
    meta: dict[str, Any] = {}
    raw_markdown: str


class GenerateResponse(BaseModel):
    exercises: list[GeneratedExercise]
    count_requested: int
    count_returned: int
    ab_variant: str | None = None


class SaveRequest(BaseModel):
    exercises: list[GeneratedExercise]
    content_dir: str = "content"


class SaveResponse(BaseModel):
    saved: list[str]
    skipped: list[str]
