from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from sqlmodel import Session, create_engine, select

from app.exams.models import Exam, ExamTopic, StudyBlock, StudyBlockKind
from app.exams.planner import build_plan
from app.exams.schemas import PlannerOptions
from app.models import User, app_metadata


def _setup_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    app_metadata.create_all(engine)
    return engine


def test_build_plan_respects_cap_and_inserts_mocks():
    engine = _setup_engine()
    with Session(engine) as session:
        user = User(id=uuid4(), timezone="Europe/Helsinki", streak_days=0, persona="Calm")
        session.add(user)
        session.flush()

        exam = Exam(
            user_id=user.id,
            title="Physics Midterm",
            course="Physics",
            exam_at=datetime.utcnow() + timedelta(days=9),
            target_grade=5,
        )
        session.add(exam)
        session.flush()

        topics = [
            ExamTopic(exam_id=exam.id, name="Kinematics", est_minutes=150, priority=3, dependencies=[]),
            ExamTopic(exam_id=exam.id, name="Dynamics", est_minutes=120, priority=2, dependencies=["Kinematics"]),
            ExamTopic(exam_id=exam.id, name="Energy", est_minutes=90, priority=2, dependencies=[]),
        ]
        for topic in topics:
            session.add(topic)
        session.flush()

        opts = PlannerOptions(buffer_days=2, daily_cap_min=180, min_block=25, mock_count=2, interleave_ratio=0.5)
        today = datetime.utcnow().date()
        plan, _ = build_plan(session, exam, topics, "spaced_structured", opts)
        session.commit()

        blocks = session.exec(select(StudyBlock).where(StudyBlock.plan_id == plan.id)).all()
        assert blocks

        horizon_end = exam.exam_at.date() - timedelta(days=opts.buffer_days)
        day_totals = {}
        mock_blocks = []
        topic_touch_counts = {topic.name: 0 for topic in topics}

        for block in blocks:
            assert block.day >= today
            assert block.day <= horizon_end
            day_totals.setdefault(block.day, 0)
            day_totals[block.day] += block.minutes
            if block.kind == StudyBlockKind.MOCK:
                mock_blocks.append(block)
            if block.topic in topic_touch_counts and block.kind in {
                StudyBlockKind.LEARN,
                StudyBlockKind.REVIEW,
                StudyBlockKind.DRILL,
            }:
                topic_touch_counts[block.topic] += 1

        for total in day_totals.values():
            assert total <= opts.daily_cap_min or total <= opts.daily_cap_min + opts.min_block

        assert len(mock_blocks) == opts.mock_count
        for mock in mock_blocks:
            assert mock.day >= horizon_end - timedelta(days=6)

        for topic in topics:
            if topic.est_minutes >= 60:
                assert topic_touch_counts[topic.name] >= 3
