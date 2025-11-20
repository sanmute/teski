from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import MetaData
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field, SQLModel


app_metadata = MetaData()


def _utcnow() -> datetime:
    return datetime.utcnow()


class AppSQLModel(SQLModel, table=False):
    """Base class binding models to app_metadata."""

    __abstract__ = True
    metadata = app_metadata


class MistakeSubtype(str, Enum):
    NEAR_MISS = "near_miss"
    SIGN = "sign"
    UNIT = "unit"
    ROUNDING = "rounding"
    CONCEPTUAL = "conceptual"
    OTHER = "other"


class User(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=_utcnow, index=True)
    timezone: str = Field(default="UTC")
    display_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None, index=True)
    streak_days: int = Field(default=0, ge=0)
    last_streak_at: Optional[datetime] = Field(default=None, index=True)
    persona: Optional[str] = Field(default=None, index=True)
    is_pro: bool = Field(default=False, index=True)
    pro_until: Optional[datetime] = Field(default=None, index=True)
    institution_id: Optional[UUID] = Field(default=None, foreign_key="institution.id", index=True)
    analytics_consent: bool = Field(default=True)
    is_institution_admin: bool = Field(default=False, index=True)


class Task(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str
    course: Optional[str] = Field(default=None, index=True)
    due_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow, index=True)


class MemoryItem(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    task_id: Optional[UUID] = Field(default=None, foreign_key="task.id", index=True)
    concept: str = Field(index=True)
    ease: float = Field(default=2.5)
    interval: int = Field(default=1, ge=0)
    due_at: datetime = Field(index=True)
    stability: float = Field(default=0.0)
    difficulty: float = Field(default=0.3)
    lapses: int = Field(default=0, ge=0)


class Mistake(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    task_id: Optional[UUID] = Field(default=None, foreign_key="task.id", index=True)
    concept: str = Field(index=True)
    subtype: MistakeSubtype = Field(default=MistakeSubtype.OTHER, index=True)
    raw: str
    created_at: datetime = Field(default_factory=_utcnow, index=True)


class ReviewLog(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    memory_id: UUID = Field(foreign_key="memoryitem.id", index=True)
    grade: int = Field(default=0, ge=0, le=5)
    scheduled_for: datetime = Field(index=True)
    reviewed_at: datetime = Field(index=True)
    next_due_at: datetime = Field(index=True)
    delta_seconds: int = Field(default=0)


class PersonaState(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    persona: str = Field(index=True)
    warmup_ts: Optional[datetime] = Field(default=None, index=True)


class Badge(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    kind: str = Field(index=True)
    acquired_at: datetime = Field(default_factory=_utcnow, index=True)


class ABTestAssignment(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    experiment: str = Field(index=True)
    bucket: str = Field(index=True)
    assigned_at: datetime = Field(default_factory=_utcnow, index=True)


class AnalyticsEvent(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id", index=True)
    kind: str = Field(index=True)
    payload: dict = Field(default_factory=dict, sa_type=JSON)
    ts: datetime = Field(default_factory=_utcnow, index=True)


class XPEvent(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    amount: int = Field(default=0)
    reason: str = Field(index=True)
    ts: datetime = Field(default_factory=_utcnow, index=True)


class LegacyUserMap(AppSQLModel, table=True):
    __tablename__ = "legacy_user_map"
    legacy_user_id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)


class LegacyTaskMap(AppSQLModel, table=True):
    __tablename__ = "legacy_task_map"
    legacy_task_id: str = Field(primary_key=True)
    task_id: UUID = Field(foreign_key="task.id", index=True)


try:
    import app.analytics.models  # noqa: F401  # ensures metadata registration
except ImportError:
    pass

try:
    import app.deep.models  # noqa: F401
    import app.prefs.models  # noqa: F401
except ImportError:
    pass

try:
    import app.pilot.models  # noqa: F401
except ImportError:
    pass

try:
    import app.learner.models  # noqa: F401
except ImportError:
    pass

try:
    import app.tasks.models  # noqa: F401
except ImportError:
    pass

try:
    import app.notifications.models  # noqa: F401
except ImportError:
    pass

try:
    import app.study.models  # noqa: F401
except ImportError:
    pass

try:
    import app.integrations.models  # noqa: F401
except ImportError:
    pass

try:
    import app.mastery.models  # noqa: F401
except ImportError:
    pass

try:
    import app.institutions.models  # noqa: F401
except ImportError:
    pass


class PracticeSession(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    skill_id: Optional[UUID] = Field(default=None, foreign_key="skill.id", index=True)
    length: int = Field(default=0, ge=0)
    correct_count: int = Field(default=0, ge=0)
    incorrect_count: int = Field(default=0, ge=0)
    avg_difficulty: float = Field(default=0.0)
    fraction_review: float = Field(default=0.0)
    started_at: datetime = Field(default_factory=_utcnow, index=True)
    finished_at: datetime = Field(default_factory=_utcnow, index=True)
    abandoned: bool = Field(default=False, index=True)


class BehavioralProfile(AppSQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="user.id", unique=True, index=True)
    engagement_level: float = Field(default=0.0)
    consistency_score: float = Field(default=0.0)
    challenge_preference: float = Field(default=50.0)
    review_vs_new_bias: float = Field(default=50.0)
    session_length_preference: float = Field(default=50.0)
    fatigue_risk: float = Field(default=10.0)
    updated_at: datetime = Field(default_factory=_utcnow, index=True)
