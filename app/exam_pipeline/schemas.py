from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class PipelineRequest(BaseModel):
    course_name: str
    course_code: str | None = None
    pdf_urls: list[str]
    num_exercises: int = 10
    exercise_types: list[str] = ["mcq", "numeric", "short_answer"]
    difficulty_min: int = 1
    difficulty_max: int = 4

    @field_validator("pdf_urls")
    @classmethod
    def validate_pdf_urls(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("pdf_urls must contain at least one URL")
        if len(v) > 3:
            raise ValueError("pdf_urls must contain at most 3 URLs")
        return v

    @field_validator("num_exercises")
    @classmethod
    def validate_num_exercises(cls, v: int) -> int:
        if not 1 <= v <= 20:
            raise ValueError("num_exercises must be between 1 and 20")
        return v

    @field_validator("exercise_types")
    @classmethod
    def validate_exercise_types(cls, v: list[str]) -> list[str]:
        allowed = {"mcq", "numeric", "short_answer"}
        if not v:
            raise ValueError("exercise_types must not be empty")
        invalid = [t for t in v if t not in allowed]
        if invalid:
            raise ValueError(
                f"Invalid exercise types: {invalid!r}. Allowed: {sorted(allowed)!r}"
            )
        return v

    @field_validator("difficulty_min", "difficulty_max")
    @classmethod
    def validate_difficulty(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("difficulty must be between 1 and 5")
        return v

    @model_validator(mode="after")
    def validate_difficulty_range(self) -> "PipelineRequest":
        if self.difficulty_min > self.difficulty_max:
            raise ValueError("difficulty_min must not exceed difficulty_max")
        return self


class GeneratedExerciseOut(BaseModel):
    id: str
    concept: str
    type: str
    question: str
    difficulty: int
    skill_ids: list[str]
    keywords: list[str]
    course: str | None
    domain: str | None
    meta: dict[str, Any]
    explanation: str
    raw_markdown: str


class PipelineResponse(BaseModel):
    course_name: str
    exercises: list[GeneratedExerciseOut]
    pdf_count: int
    source_urls: list[str]
