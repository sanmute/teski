from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

from app.main import create_app
from app.models import AnalyticsEvent, MemoryItem, Mistake, XPEvent, app_metadata
from app.db import get_session as app_get_session
from app import db as app_db
from app import config as app_config
from app.ex_api import _exercise_index, _reset_rate_limit


@pytest.fixture()
def api_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    app_metadata.create_all(engine)

    app_config.get_settings.cache_clear()
    new_settings = app_config.get_settings()
    new_settings.DEV_MODE = True

    monkeypatch.setattr(app_db, "engine", engine)
    monkeypatch.setattr(app_db, "settings", new_settings)

    import app.scheduler as scheduler

    monkeypatch.setattr(scheduler, "settings", new_settings)

    def get_session_override():
        with Session(engine) as session:
            yield session

    application = create_app()
    application.dependency_overrides[app_get_session] = get_session_override

    import app.exercises as exercises_module

    exercises_module._EXERCISE_CACHE = None
    _exercise_index.cache_clear()
    _reset_rate_limit()

    with TestClient(application) as client:
        yield client, engine

    application.dependency_overrides.clear()
    app_config.get_settings.cache_clear()


def _count(session: Session, model):
    return session.exec(select(model)).all()


def test_submit_incorrect_logs_mistake_and_memory(api_client):
    client, engine = api_client
    user_id = uuid4()

    response = client.post(
        "/ex/submit",
        params={"id": "ee.ohm.current.calc", "user_id": str(user_id)},
        json={"value": 99.0, "unit": "A"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is False
    assert body["next_hint"]

    with Session(engine) as session:
        mistakes = _count(session, Mistake)
        memories = _count(session, MemoryItem)
        assert len(mistakes) == 1
        assert len(memories) == 1


def test_submit_correct_awards_xp(api_client):
    client, engine = api_client
    user_id = uuid4()

    response = client.post(
        "/ex/submit",
        params={"id": "ee.ohm.current.calc", "user_id": str(user_id)},
        json={"value": 4.0, "unit": "A"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True

    with Session(engine) as session:
        xp_events = _count(session, XPEvent)
        mistakes = _count(session, Mistake)
        assert len(xp_events) == 1
        assert xp_events[0].reason == "exercise_correct"
        assert mistakes == []


def test_submit_invalid_payload_returns_422(api_client):
    client, engine = api_client
    user_id = uuid4()

    response = client.post(
        "/ex/submit",
        params={"id": "ee.kvl.loop-sum.zero", "user_id": str(user_id)},
        json={"choice": "first"},
    )
    assert response.status_code == 422

    with Session(engine) as session:
        assert _count(session, Mistake) == []
        assert _count(session, AnalyticsEvent) == []


def test_submit_rate_limit_blocks_excess_requests(api_client):
    client, engine = api_client
    user_id = uuid4()

    for _ in range(30):
        resp = client.post(
            "/ex/submit",
            params={"id": "ee.ohm.current.calc", "user_id": str(user_id)},
            json={"value": 99.0},
        )
        assert resp.status_code == 200

    resp = client.post(
        "/ex/submit",
        params={"id": "ee.ohm.current.calc", "user_id": str(user_id)},
        json={"value": 99.0},
    )
    assert resp.status_code == 429

    with Session(engine) as session:
        assert len(_count(session, Mistake)) >= 30
