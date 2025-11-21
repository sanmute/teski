from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import Session, create_engine, select

from app.learning_trajectory_service import (
    record_session_summary,
    snapshot_mastery_after_session,
    get_skill_trajectory,
    detect_stagnant_skills,
    summarize_recent_trends,
)
from app.mastery.models import Skill, UserSkillMastery
from app.models import User, app_metadata


def setup_db():
    engine = create_engine("sqlite://", echo=False)
    app_metadata.create_all(engine)
    return engine


def create_user_and_skill(session: Session):
    user = User(id=uuid4(), timezone="UTC", streak_days=0)
    skill = Skill(name="Test Skill", slug="test-skill")
    session.add(user)
    session.add(skill)
    session.commit()
    session.refresh(user)
    session.refresh(skill)
    return user, skill


def test_record_session_summary_and_snapshot():
    engine = setup_db()
    with Session(engine) as session:
        user, skill = create_user_and_skill(session)
        session.add(UserSkillMastery(user_id=user.id, skill_id=skill.id, mastery=10.0))
        session.commit()

        results = [
            {"skill_ids": [skill.id], "is_correct": True, "difficulty": 2, "mistake_type": None, "is_review": False},
            {"skill_ids": [skill.id], "is_correct": False, "difficulty": 3, "mistake_type": "math_concept:sign_error", "is_review": True},
        ]
        summary = record_session_summary(
            session,
            user_id=user.id,
            micro_quest_id="mq1",
            exercise_results=results,
            xp_gained=50,
        )
        session.commit()
        assert summary.num_exercises == 2
        assert summary.num_correct == 1
        assert summary.mistake_type_counts.get("math_concept:sign_error") == 1

        snaps = snapshot_mastery_after_session(session, user_id=user.id, skill_ids=[skill.id], exercise_results=results)
        session.commit()
        assert len(snaps) == 1
        assert snaps[0].num_attempts == 2
        assert snaps[0].num_correct == 1
        assert "math_concept:sign_error" in (snaps[0].dominant_mistake_subtypes or [])


def test_trajectory_and_stagnation_detection():
    engine = setup_db()
    with Session(engine) as session:
        user, skill = create_user_and_skill(session)
        # Add mastery record
        session.add(UserSkillMastery(user_id=user.id, skill_id=skill.id, mastery=50.0))
        session.commit()

        # Add snapshots with small deltas
        # day 1
        snapshot_mastery_after_session(session, user_id=user.id, skill_ids=[skill.id], timestamp=datetime.utcnow() - timedelta(days=2))
        # simulate slight change
        usm = session.exec(
            select(UserSkillMastery).where(UserSkillMastery.user_id == user.id, UserSkillMastery.skill_id == skill.id)
        ).one()
        usm.mastery += 0.005
        session.add(usm)
        session.commit()
        snapshot_mastery_after_session(session, user_id=user.id, skill_ids=[skill.id], timestamp=datetime.utcnow() - timedelta(days=1))
        session.commit()

        traj = get_skill_trajectory(session, user.id, skill.id, days_back=5)
        assert len(traj) >= 2

        stagnant = detect_stagnant_skills(session, user.id, min_days=3, delta_threshold=0.05)
        assert isinstance(stagnant, list)

        trends = summarize_recent_trends(session, user.id, days_back=7)
        assert "stagnant_skills" in trends
