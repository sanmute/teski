# >>> LEADERBOARD START SCHEMAS
"""Pydantic schemas for leaderboard endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict


class LeaderboardCreate(BaseModel):
    name: str
    course_id: Optional[str] = None


class JoinLeaderboard(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class AwardPoints(BaseModel):
    event_type: str
    points: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


class MemberConsent(BaseModel):
    display_consent: bool


class LeaderboardOut(BaseModel):
    id: int
    name: str
    course_id: Optional[str]
    join_code: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberOut(BaseModel):
    user_id: int
    display_name: Optional[str]
    anon_handle: str
    display_consent: bool
    weekly_points: int
    total_points: int
    streak_days: int


class LeaderboardStandings(BaseModel):
    """Serialized leaderboard standings response.

    Example:
        {
          "leaderboard": {
            "id": 12,
            "name": "LUT TIES23",
            "course_id": "CS101",
            "join_code": "K7P9GZB",
            "created_at": "2025-09-28T09:00:00Z"
          },
          "week": {
            "year": 2025,
            "number": 39,
            "start": "2025-09-22T00:00:00+03:00",
            "end": "2025-09-29T00:00:00+03:00"
          },
          "members": [
            {
              "user_id": 3,
              "display_name": null,
              "anon_handle": "an_Q4X7M2A9D",
              "display_consent": false,
              "weekly_points": 35,
              "total_points": 120,
              "streak_days": 4
            }
          ]
        }
    """

    leaderboard: LeaderboardOut
    week: Dict[str, Any]
    members: List[MemberOut]


class PointsEventOut(BaseModel):
    id: int
    event_type: str
    points: int
    occurred_at: datetime
    meta: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)
# >>> LEADERBOARD END SCHEMAS
