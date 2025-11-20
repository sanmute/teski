from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models import BehavioralProfile, PracticeSession
from app.timeutil import _utcnow

MAX_SESSION_LOOKBACK_DAYS = 30
MAX_SESSION_RECORDS = 60


def _recent_sessions(session: Session, user_id: UUID) -> List[PracticeSession]:
    cutoff = _utcnow() - timedelta(days=MAX_SESSION_LOOKBACK_DAYS)
    stmt = (
        select(PracticeSession)
        .where(PracticeSession.user_id == user_id, PracticeSession.started_at >= cutoff)
        .order_by(PracticeSession.started_at.desc())
        .limit(MAX_SESSION_RECORDS)
    )
    return list(session.exec(stmt).all())


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _engagement_score(sessions: List[PracticeSession]) -> float:
    week_cutoff = _utcnow() - timedelta(days=7)
    recent = [s for s in sessions if s.finished_at >= week_cutoff]
    score = (len(recent) / 14.0) * 100.0
    return _clamp(score)


def _consistency_score(sessions: List[PracticeSession]) -> float:
    week_cutoff = _utcnow() - timedelta(days=7)
    days = {s.finished_at.date() for s in sessions if s.finished_at >= week_cutoff}
    score = (len(days) / 6.0) * 100.0
    return _clamp(score)


def _challenge_preference(sessions: List[PracticeSession]) -> float:
    if not sessions:
        return 50.0
    window = sessions[:10]
    avg_diff = sum(s.avg_difficulty for s in window) / len(window)
    base = 20.0 + ((avg_diff - 1.0) * 20.0)
    total_correct = sum(s.correct_count for s in window)
    total_attempts = sum(max(1, s.length) for s in window)
    correct_rate = total_correct / total_attempts if total_attempts else 0.0
    if correct_rate > 0.8:
        base += 10
    elif correct_rate < 0.5:
        base -= 10
    return _clamp(base)


def _review_bias(sessions: List[PracticeSession]) -> float:
    if not sessions:
        return 50.0
    window = sessions[:10]
    avg_fraction = sum(s.fraction_review for s in window) / len(window)
    return _clamp(avg_fraction * 100.0)


def _session_length_preference(sessions: List[PracticeSession]) -> float:
    if not sessions:
        return 50.0
    window = sessions[:10]
    avg_length = sum(s.length for s in window) / len(window)
    return _clamp((avg_length / 10.0) * 100.0)


def _fatigue_risk(sessions: List[PracticeSession]) -> float:
    cutoff = _utcnow() - timedelta(days=3)
    recent = [s for s in sessions if s.finished_at >= cutoff]
    total_questions = sum(s.length for s in recent)
    total_correct = sum(s.correct_count for s in recent)
    correct_rate = total_correct / total_questions if total_questions else 1.0
    if total_questions > 120:
        return 95.0 if correct_rate < 0.6 else 80.0
    if total_questions > 80:
        return 70.0 if correct_rate < 0.6 else 55.0
    if total_questions > 50:
        return 40.0
    return 20.0


def update_behavioral_profile(db: Session, user_id: UUID) -> BehavioralProfile:
    sessions = _recent_sessions(db, user_id)
    profile = (
        db.exec(select(BehavioralProfile).where(BehavioralProfile.user_id == user_id)).one_or_none()
    )
    if profile is None:
        profile = BehavioralProfile(user_id=user_id)
        db.add(profile)

    profile.engagement_level = _engagement_score(sessions)
    profile.consistency_score = _consistency_score(sessions)
    profile.challenge_preference = _challenge_preference(sessions)
    profile.review_vs_new_bias = _review_bias(sessions)
    profile.session_length_preference = _session_length_preference(sessions)
    profile.fatigue_risk = _fatigue_risk(sessions)
    profile.updated_at = _utcnow()
    db.add(profile)
    db.flush()
    return profile


def get_behavior_profile(db: Session, user_id: UUID) -> BehavioralProfile:
    profile = (
        db.exec(select(BehavioralProfile).where(BehavioralProfile.user_id == user_id)).one_or_none()
    )
    if profile is None:
        profile = update_behavioral_profile(db, user_id)
    return profile


def recommend_session_length(profile: Optional[BehavioralProfile]) -> int:
    if profile is None:
        return 5
    if profile.fatigue_risk >= 70:
        return 3
    if profile.session_length_preference >= 70 and profile.fatigue_risk < 50:
        return 7
    if profile.session_length_preference <= 30:
        return 3
    return 5
