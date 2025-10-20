from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlmodel import Session, create_engine, select

from app.abtest import assign_and_persist
from app.models import ABTestAssignment, User, app_metadata


def _init_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    app_metadata.create_all(engine)
    return engine


def test_assign_and_persist_reuses_existing_bucket():
    engine = _init_engine()
    with Session(engine) as session:
        user = User(id=uuid4(), created_at=datetime.utcnow(), timezone="UTC", streak_days=0, persona="Calm")
        session.add(user)
        session.commit()
        session.refresh(user)

        bucket = assign_and_persist(session, user.id, "ui_experiment")
        session.commit()
        assert bucket in {"control", "variant_a"}

        repeat_bucket = assign_and_persist(session, user.id, "ui_experiment")
        session.commit()
        assert repeat_bucket == bucket

        assignments = session.exec(select(ABTestAssignment)).all()
        assert len(assignments) == 1
        assert assignments[0].bucket == bucket
