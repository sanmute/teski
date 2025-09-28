# >>> LEADERBOARD START MODELS
"""SQLModel tables backing the leaderboard feature."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import SQLModel, Field, Relationship, Column

from backend.utils.time import now_utc


class Leaderboard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    course_id: Optional[str] = Field(default=None, index=True)
    join_code: str = Field(index=True, sa_column_kwargs={"unique": True, "nullable": False})
    created_at: datetime = Field(default_factory=now_utc)
    creator_user_id: int = Field(foreign_key="user.id")

    members: list["LeaderboardMember"] = Relationship(back_populates="leaderboard")


class LeaderboardMember(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("leaderboard_id", "user_id", name="uq_leaderboard_member"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    leaderboard_id: int = Field(foreign_key="leaderboard.id")
    user_id: int = Field(foreign_key="user.id")
    joined_at: datetime = Field(default_factory=now_utc)
    display_consent: bool = Field(default=False)

    leaderboard: Optional[Leaderboard] = Relationship(back_populates="members")


class PointsEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    leaderboard_id: int = Field(foreign_key="leaderboard.id")
    user_id: int = Field(foreign_key="user.id")
    event_type: str
    points: int
    occurred_at: datetime = Field(default_factory=now_utc)
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))


class WeeklyScore(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "leaderboard_id",
            "user_id",
            "week_year",
            "week_number",
            name="uq_weekly_score",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    leaderboard_id: int = Field(foreign_key="leaderboard.id")
    user_id: int = Field(foreign_key="user.id")
    week_year: int
    week_number: int
    points: int = Field(default=0)
# >>> LEADERBOARD END MODELS
