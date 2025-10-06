# >>> DFE START
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, UniqueConstraint


class SkillNode(SQLModel, table=True):
    """Represents a skill node in a versioned prerequisite graph."""

    __tablename__ = "skill_nodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, description="Canonical identifier e.g. math.integrals.substitution")
    title: str
    graph_version: str = Field(default="v1", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("key", "graph_version", name="uq_skill_key_version"),)


class SkillEdge(SQLModel, table=True):
    """Directed edge encoding prerequisite relationships between skills."""

    __tablename__ = "skill_edges"

    id: Optional[int] = Field(default=None, primary_key=True)
    from_skill_id: int = Field(index=True, foreign_key="skill_nodes.id")
    to_skill_id: int = Field(index=True, foreign_key="skill_nodes.id")


class TaskTypeEnum(str, Enum):
    NUMERIC = "numeric"
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_TEXT = "short_text"


class TaskTemplate(SQLModel, table=True):
    """Parametric template defining deterministic task instances."""

    __tablename__ = "task_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, description="Human-readable template code e.g. math.integrals.subst.01")
    title: str
    skill_id: int = Field(foreign_key="skill_nodes.id")
    task_type: TaskTypeEnum = Field(default=TaskTypeEnum.NUMERIC)
    text_template: str
    parameters: Dict[str, Any] = Field(sa_column=Column(JSON))
    constraints: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    answer_spec: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("code", name="uq_task_template_code"),)


class TaskInstance(SQLModel, table=True):
    """Concrete realisation of a template for a specific learner."""

    __tablename__ = "task_instances"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="task_templates.id", index=True)
    user_id: int = Field(index=True)
    seed: str = Field(index=True, description="Deterministic seed used to generate params")
    params: Dict[str, Any] = Field(sa_column=Column(JSON))
    rendered_text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("template_id", "user_id", "seed", name="uq_instance_template_user_seed"),)


class TaskAttempt(SQLModel, table=True):
    """Single attempt from a learner for a generated instance."""

    __tablename__ = "task_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)
    instance_id: int = Field(foreign_key="task_instances.id", index=True)
    user_id: int = Field(index=True)
    submitted_answer: Any = Field(sa_column=Column(JSON))
    is_correct: bool = Field(index=True)
    latency_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SkillMastery(SQLModel, table=True):
    """Simple EWMA-based mastery tracking per user and skill."""

    __tablename__ = "skill_mastery"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    skill_id: int = Field(foreign_key="skill_nodes.id", index=True)
    mastery: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)
# <<< DFE END
