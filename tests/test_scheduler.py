import os
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_memory.db")
os.environ.setdefault("DAILY_REVIEW_CAP", "3")

from app.config import get_settings
from app.models import MemoryItem, ReviewLog, User, app_metadata
from app.scheduler import enforce_daily_cap, review, schedule_from_mistake


@pytest.fixture()
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    app_metadata.create_all(engine)
    return engine


@pytest.fixture()
def user(engine):
    with Session(engine) as session:
        user = User(id=uuid4(), created_at=datetime.utcnow(), timezone="UTC", streak_days=0, persona="Calm")
        session.add(user)
        session.commit()
        session.refresh(user)
        yield user


def test_schedule_and_review_progression(engine, user):
    with Session(engine) as session:
        memory = schedule_from_mistake(session, user=user, concept="algebra")
        session.commit()
        assert memory.due_at > datetime.utcnow()
        baseline_interval = memory.interval

        review(session, user, memory, grade=5)
        session.commit()
        assert memory.interval >= baseline_interval
        assert memory.ease >= 2.5


def test_enforce_daily_cap(engine, user):
    with Session(engine) as session:
        get_settings().DAILY_REVIEW_CAP = 3
        memory = MemoryItem(
            id=uuid4(),
            user_id=user.id,
            concept="geometry",
            ease=2.5,
            interval=1,
            due_at=datetime.utcnow(),
            stability=0.0,
            difficulty=0.3,
            lapses=0,
        )
        session.add(memory)
        session.commit()

        # Initially we should have full cap available
        assert enforce_daily_cap(session, user, 2) == 2

        for _ in range(3):
            log = ReviewLog(
                id=uuid4(),
                user_id=user.id,
                memory_id=memory.id,
                grade=4,
                scheduled_for=datetime.utcnow(),
                reviewed_at=datetime.utcnow(),
                next_due_at=datetime.utcnow(),
                delta_seconds=30,
            )
            session.add(log)
        session.commit()

        # With cap set to 3, no reviews should be permitted now
        assert enforce_daily_cap(session, user, 2) == 0
