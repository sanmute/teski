from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

from app.main import create_app
from app import config as app_config
from app import db as app_db
from app.db import get_session as app_get_session
from app.exams.models import StudyBlockStatus
from app.models import User, XPEvent, app_metadata


@pytest.fixture()
def api_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    app_metadata.create_all(engine)

    app_config.get_settings.cache_clear()
    settings = app_config.get_settings()
    settings.DEV_MODE = True
    settings.EX_AGENDA_REVIEW_FIRST = True

    monkeypatch.setattr(app_db, "engine", engine)
    monkeypatch.setattr(app_db, "settings", settings)

    import app.scheduler as scheduler

    monkeypatch.setattr(scheduler, "settings", settings)

    def override_session():
        with Session(engine) as session:
            yield session

    application = create_app()
    application.dependency_overrides[app_get_session] = override_session

    with TestClient(application) as client:
        yield client, engine

    application.dependency_overrides.clear()
    app_config.get_settings.cache_clear()


def test_exam_flow_creates_plan_and_awards_xp(api_client):
    client, engine = api_client
    user_id = uuid4()
    with Session(engine) as session:
        session.add(User(id=user_id, timezone="Europe/Helsinki", streak_days=0, persona="Calm"))
        session.commit()

    exam_payload = {
        "user_id": str(user_id),
        "title": "EE Midterm",
        "course": "Basics of EE",
        "exam_at": (datetime.utcnow() + timedelta(days=10)).isoformat(),
    }
    exam_resp = client.post("/exam/create", json=exam_payload)
    assert exam_resp.status_code == 200
    exam_id = exam_resp.json()["id"]

    topics_payload = [
        {"name": "KCL", "est_minutes": 120},
        {"name": "KVL", "est_minutes": 120, "dependencies": ["KCL"]},
        {"name": "Ohm", "est_minutes": 90},
    ]
    topics_resp = client.post(f"/exam/{exam_id}/topics", json=topics_payload)
    assert topics_resp.status_code == 200
    assert len(topics_resp.json()) == 3

    questionnaire_resp = client.post(
        f"/exam/{exam_id}/questionnaire",
        json={"style": "auto", "answers": {"pref_practice": 5, "cram_history": 2}},
    )
    assert questionnaire_resp.status_code == 200
    style = questionnaire_resp.json()["style"]
    assert style in {"spaced_structured", "cram_then_revise", "interleaved_hands_on", "theory_first"}

    plan_resp = client.post(
        f"/exam/{exam_id}/plan",
        json={"daily_cap_min": 150, "mock_count": 1, "buffer_days": 2},
    )
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    blocks = plan_data["blocks"]
    assert blocks

    plan_get = client.get(f"/exam/{exam_id}/plan")
    assert plan_get.status_code == 200
    assert plan_get.json()["id"] == plan_data["id"]

    today_resp = client.get(f"/exam/{exam_id}/today", params={"user_id": str(user_id)})
    assert today_resp.status_code == 200
    assert isinstance(today_resp.json(), list)

    first_block = blocks[0]
    progress_resp = client.post(
        "/exam/block/progress",
        json={
            "block_id": first_block["id"],
            "status": "done",
            "minutes_spent": first_block["minutes"],
        },
    )
    assert progress_resp.status_code == 200
    assert progress_resp.json()["status"] == StudyBlockStatus.DONE.value

    with Session(engine) as session:
        xp_events = session.exec(select(XPEvent).where(XPEvent.user_id == user_id)).all()
        assert xp_events
        assert any(event.reason == "study_block_done" for event in xp_events)
