from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Column
from sqlalchemy.types import JSON, TEXT
from sqlmodel import Field, SQLModel


class Exercise(SQLModel, table=True):
    """Canonical exercise record seeded from JSON files."""

    __tablename__ = "exercises"

    id: str = Field(sa_column=Column(TEXT, primary_key=True, nullable=False))
    question_text: str
    type: str = Field(index=True)
    choices: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    correct_answer: str
    difficulty: int = Field(default=1, index=True)
    skill_ids: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    solution_explanation: Optional[str] = None
    hint: Optional[str] = None
    meta: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # JSON serialization helpers -------------------------------------------------
    def to_dict(self, include_answer: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "question_text": self.question_text,
            "type": self.type,
            "choices": self.choices or [],
            "difficulty": self.difficulty,
            "skill_ids": self.skill_ids or [],
            "solution_explanation": self.solution_explanation,
            "hint": self.hint,
            "metadata": self.meta or {},
        }
        if include_answer:
            data["correct_answer"] = self.correct_answer
        return data
