import os
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine, select

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_memory.db")

from app.badges import check_nemesis
from app.models import Badge, MemoryItem, ReviewLog, User, app_metadata


@pytest.fixture()
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    app_metadata.create_all(engine)
    return engine


def test_nemesis_badge_award(engine):
    with Session(engine) as session:
        user = User(id=uuid4(), created_at=datetime.utcnow(), timezone="UTC", streak_days=0, persona="Calm")
        session.add(user)
        session.commit()
        session.refresh(user)

        memory = MemoryItem(
            id=uuid4(),
            user_id=user.id,
            concept="physics",
            ease=2.5,
            interval=1,
            due_at=datetime.utcnow(),
            stability=0.0,
            difficulty=0.3,
            lapses=2,
        )
        session.add(memory)
        session.commit()

        now = datetime.utcnow()
        for idx in range(3):
            log = ReviewLog(
                id=uuid4(),
                user_id=user.id,
                memory_id=memory.id,
                grade=4,
                scheduled_for=now - timedelta(minutes=10 * (idx + 1)),
                reviewed_at=now - timedelta(minutes=idx),
                next_due_at=now + timedelta(days=idx + 1),
                delta_seconds=45,
            )
            session.add(log)
        session.commit()

        assert check_nemesis(user, "physics", session=session)
        # Second call should be idempotent
        assert check_nemesis(user, "physics", session=session)
        badges = session.exec(select(Badge).where(Badge.user_id == user.id)).all()
        assert len(badges) == 1
