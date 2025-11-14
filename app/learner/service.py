from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from .models import LearnerProfile

SAFE_DEFAULTS: dict[str, Any] = {
    "approach_new_topic": "skim_first",
    "stuck_strategy": "search_online",
    "explanation_style": "step_by_step",
    "confidence_baseline": 3,
    "long_assignment_reaction": "motivated",
    "focus_time": "morning",
    "communication_style": "normal",
    "practice_style": "mixed",
    "time_estimation_bias": "accurate",
    "analytical_comfort": 3,
    "feedback_preference": "supportive",
    "challenges": [],
    "primary_device": "laptop",
    "proactivity_level": "medium",
    "semester_goal": "improve_grades",
}


def get_learner_profile(session: Session, user_id: UUID) -> LearnerProfile | None:
    return session.exec(select(LearnerProfile).where(LearnerProfile.user_id == user_id)).first()


def get_or_default_profile(session: Session, user_id: UUID) -> LearnerProfile:
    profile = get_learner_profile(session, user_id)
    if profile is not None:
        return profile
    defaults = deepcopy(SAFE_DEFAULTS)
    return LearnerProfile(user_id=user_id, **defaults)
