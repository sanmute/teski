from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.mastery.models import Skill, UserSkillMastery
from app.mastery.service import get_mastery_record
from app.models import (
    SessionSummary,
    UserSkillMasterySnapshot,
    UserWeeklySummary,
)


def _today(date: Optional[datetime] = None) -> datetime:
    dt = date or datetime.utcnow()
    return datetime(dt.year, dt.month, dt.day)


def record_session_summary(
    session: Session,
    *,
    user_id: UUID,
    micro_quest_id: Optional[str],
    exercise_results: Iterable[Dict[str, Any]],
    xp_gained: int = 0,
    duration_seconds: Optional[int] = None,
    streak_at_start: Optional[int] = None,
    streak_at_end: Optional[int] = None,
) -> SessionSummary:
    num_exercises = 0
    num_correct = 0
    total_difficulty = 0.0
    review_count = 0
    new_count = 0
    mistake_counter: Counter[str] = Counter()
    skills: set[str] = set()

    for result in exercise_results:
        num_exercises += 1
        if result.get("is_correct"):
            num_correct += 1
        difficulty = result.get("difficulty", 1) or 1
        total_difficulty += difficulty
        if result.get("is_review"):
            review_count += 1
        else:
            new_count += 1
        mtype = result.get("mistake_type")
        if mtype:
            mistake_counter[str(mtype)] += 1
        for sid in result.get("skill_ids", []) or []:
            skills.add(str(sid))

    avg_difficulty = (total_difficulty / num_exercises) if num_exercises else 0.0
    summary = SessionSummary(
        user_id=user_id,
        micro_quest_id=micro_quest_id,
        skill_ids=list(skills),
        num_exercises=num_exercises,
        num_correct=num_correct,
        avg_difficulty=avg_difficulty,
        xp_gained=xp_gained,
        duration_seconds=duration_seconds,
        review_count=review_count,
        new_count=new_count,
        mistake_type_counts=dict(mistake_counter),
        streak_at_start=streak_at_start,
        streak_at_end=streak_at_end,
    )
    session.add(summary)
    session.flush()
    return summary


def snapshot_mastery_after_session(
    session: Session,
    *,
    user_id: UUID,
    skill_ids: Iterable[UUID],
    timestamp: Optional[datetime] = None,
    exercise_results: Optional[Iterable[Dict[str, Any]]] = None,
) -> List[UserSkillMasterySnapshot]:
    created: List[UserSkillMasterySnapshot] = []
    day = _today(timestamp)
    mistake_counter: Dict[UUID, Counter[str]] = defaultdict(Counter)
    correct_counts: Dict[UUID, int] = defaultdict(int)
    attempt_counts: Dict[UUID, int] = defaultdict(int)

    if exercise_results:
        for result in exercise_results:
            for sid in result.get("skill_ids", []) or []:
                sid_uuid = UUID(str(sid)) if not isinstance(sid, UUID) else sid
                attempt_counts[sid_uuid] += 1
                if result.get("is_correct"):
                    correct_counts[sid_uuid] += 1
                mtype = result.get("mistake_type")
                if mtype:
                    mistake_counter[sid_uuid][str(mtype)] += 1

    for skill_id in skill_ids:
        mastery_record = get_mastery_record(session, user_id, skill_id)
        prev_snapshot = (
            session.exec(
                select(UserSkillMasterySnapshot)
                .where(
                    UserSkillMasterySnapshot.user_id == user_id,
                    UserSkillMasterySnapshot.skill_id == skill_id,
                )
                .order_by(UserSkillMasterySnapshot.date.desc())
            )
            .first()
        )
        delta = mastery_record.mastery - (prev_snapshot.mastery_level if prev_snapshot else 0.0)
        top_mistakes = [mt for mt, _ in mistake_counter.get(skill_id, Counter()).most_common(3)]
        snapshot = UserSkillMasterySnapshot(
            user_id=user_id,
            skill_id=skill_id,
            date=day,
            mastery_level=mastery_record.mastery,
            delta_since_prev=delta,
            num_correct=correct_counts.get(skill_id, 0),
            num_attempts=attempt_counts.get(skill_id, 0),
            dominant_mistake_subtypes=top_mistakes,
        )
        session.add(snapshot)
        created.append(snapshot)
    session.flush()
    return created


def get_skill_trajectory(session: Session, user_id: UUID, skill_id: UUID, days_back: int = 30) -> List[UserSkillMasterySnapshot]:
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    return (
        session.exec(
            select(UserSkillMasterySnapshot)
            .where(
                UserSkillMasterySnapshot.user_id == user_id,
                UserSkillMasterySnapshot.skill_id == skill_id,
                UserSkillMasterySnapshot.date >= cutoff,
            )
            .order_by(UserSkillMasterySnapshot.date.asc())
        ).all()
    )


def detect_stagnant_skills(
    session: Session,
    user_id: UUID,
    min_days: int = 7,
    delta_threshold: float = 0.01,
) -> List[UUID]:
    cutoff = datetime.utcnow() - timedelta(days=min_days)
    stagnant: List[UUID] = []
    skill_ids = session.exec(select(UserSkillMastery.skill_id).where(UserSkillMastery.user_id == user_id)).all()
    for sid in skill_ids:
        snapshots = (
            session.exec(
                select(UserSkillMasterySnapshot)
                .where(
                    UserSkillMasterySnapshot.user_id == user_id,
                    UserSkillMasterySnapshot.skill_id == sid,
                    UserSkillMasterySnapshot.date >= cutoff,
                )
            ).all()
        )
        if len(snapshots) < 2:
            continue
        avg_delta = sum(s.delta_since_prev for s in snapshots) / len(snapshots)
        if abs(avg_delta) <= delta_threshold:
            stagnant.append(sid)
    return stagnant


def summarize_recent_trends(session: Session, user_id: UUID, days_back: int = 7) -> Dict[str, Any]:
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    snapshots = (
        session.exec(
            select(UserSkillMasterySnapshot)
            .where(
                UserSkillMasterySnapshot.user_id == user_id,
                UserSkillMasterySnapshot.date >= cutoff,
            )
        ).all()
    )
    by_skill: Dict[UUID, List[UserSkillMasterySnapshot]] = defaultdict(list)
    for snap in snapshots:
        by_skill[snap.skill_id].append(snap)

    improving: List[UUID] = []
    regressing: List[UUID] = []
    stagnant: List[UUID] = []

    for sid, values in by_skill.items():
        total_delta = sum(s.delta_since_prev for s in values)
        if total_delta > 0.5:
            improving.append(sid)
        elif total_delta < -0.2:
            regressing.append(sid)
        else:
            stagnant.append(sid)

    mistake_counter: Counter[str] = Counter()
    for snap in snapshots:
        for entry in snap.dominant_mistake_subtypes or []:
            if isinstance(entry, (list, tuple)) and len(entry) >= 1:
                mistake_counter[str(entry[0])] += entry[1] if len(entry) > 1 else 1
            elif isinstance(entry, str):
                mistake_counter[entry] += 1

    total_sessions = session.exec(
        select(func.count()).select_from(SessionSummary).where(
            SessionSummary.user_id == user_id, SessionSummary.created_at >= cutoff
        )
    ).one()
    total_exercises = session.exec(
        select(func.coalesce(func.sum(SessionSummary.num_exercises), 0)).where(
            SessionSummary.user_id == user_id, SessionSummary.created_at >= cutoff
        )
    ).one()

    return {
        "top_improving_skills": [str(sid) for sid in improving[:5]],
        "top_regressing_skills": [str(sid) for sid in regressing[:5]],
        "stagnant_skills": [str(sid) for sid in stagnant[:5]],
        "dominant_mistake_subtypes": [mt for mt, _ in mistake_counter.most_common(5)],
        "total_sessions": int(total_sessions or 0),
        "total_exercises": int(total_exercises or 0),
    }
