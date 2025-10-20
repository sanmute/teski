import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_memory.db")
os.environ.setdefault("DAILY_REVIEW_CAP", "3")

from app.config import get_settings
from app.models import MemoryItem, ReviewLog, User, app_metadata
import app.timeutil as timeutil
from app.scheduler import enforce_daily_cap, review, schedule_from_mistake, _update_streak, _reviews_today
from app.timeutil import user_day_bounds


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
        user = session.get(User, user.id)
        user.timezone = "Europe/Helsinki"
        session.add(user)
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

        start, _ = user_day_bounds(user.timezone)
        for offset in range(3):
            log = ReviewLog(
                id=uuid4(),
                user_id=user.id,
                memory_id=memory.id,
                grade=4,
                scheduled_for=start + timedelta(minutes=offset),
                reviewed_at=start + timedelta(minutes=offset),
                next_due_at=start + timedelta(days=1, minutes=offset),
                delta_seconds=30,
            )
            session.add(log)
        session.commit()

        # With cap set to 3, no reviews should be permitted now
        assert enforce_daily_cap(session, user, 2) == 0


def test_streak_updates_across_days(engine, user, monkeypatch):
    with Session(engine) as session:
        db_user = session.get(User, user.id)
        db_user.timezone = "America/New_York"
        session.add(db_user)

        memory = MemoryItem(
            id=uuid4(),
            user_id=db_user.id,
            concept="calculus",
            ease=2.5,
            interval=1,
            due_at=datetime.utcnow(),
            stability=0.0,
            difficulty=0.3,
            lapses=0,
        )
        session.add(memory)
        session.commit()

        def _add_logs(start: datetime) -> None:
            for offset in range(5):
                session.add(
                    ReviewLog(
                        id=uuid4(),
                        user_id=db_user.id,
                        memory_id=memory.id,
                        grade=4,
                        scheduled_for=start + timedelta(minutes=offset),
                        reviewed_at=start + timedelta(minutes=offset),
                        next_due_at=start + timedelta(days=1, minutes=offset),
                        delta_seconds=30,
                    )
                )

        day_one_now = datetime(2024, 1, 5, 17)
        day_two_now = day_one_now + timedelta(days=1)
        day_four_now = day_two_now + timedelta(days=2)

        day_one_start, _ = user_day_bounds(db_user.timezone, now=day_one_now)
        day_two_start, _ = user_day_bounds(db_user.timezone, now=day_two_now)
        day_four_start, _ = user_day_bounds(db_user.timezone, now=day_four_now)

        def _freeze(now: datetime) -> None:
            frozen = now if now.tzinfo else now.replace(tzinfo=timezone.utc)

            def _stub(dt: datetime | None = None) -> datetime:
                if dt is not None:
                    if dt.tzinfo:
                        return dt.astimezone(timezone.utc)
                    return dt.replace(tzinfo=timezone.utc)
                return frozen

            monkeypatch.setattr(timeutil, "_ensure_utc", _stub)

        _add_logs(day_one_start)
        session.commit()
        _freeze(day_one_now)
        assert _reviews_today(session, db_user) == 5
        _update_streak(session, db_user)
        session.flush()
        session.refresh(db_user)
        assert db_user.streak_days == 1
        assert db_user.last_streak_at == day_one_start

        # Additional updates the same day should not increment again
        _freeze(day_one_now)
        _update_streak(session, db_user)
        session.flush()
        session.refresh(db_user)
        assert db_user.streak_days == 1

        _add_logs(day_two_start)
        session.commit()
        _freeze(day_two_now)
        _update_streak(session, db_user)
        session.flush()
        session.refresh(db_user)
        assert db_user.streak_days == 2
        assert db_user.last_streak_at == day_two_start

        # Skip a day to ensure the streak resets
        _add_logs(day_four_start)
        session.commit()
        _freeze(day_four_now)
        _update_streak(session, db_user)
        session.flush()
        session.refresh(db_user)
        assert db_user.streak_days == 1
        assert db_user.last_streak_at == day_four_start
