# >>> LEADERBOARD START TESTS
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

import backend.models  # noqa: F401 ensures models registered
import backend.models_leaderboard  # noqa: F401
from backend.main import app
from backend.db import get_session
from backend.models import User
from backend.core.leaderboard_constants import DEFAULT_EVENT_POINTS
from backend.services import leaderboard as leaderboard_service
from backend.utils import time as time_utils


@pytest.fixture()
def test_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(test_engine):
    def get_session_override():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _create_user(engine, email: str, display_name: str | None = None) -> User:
    with Session(engine) as session:
        user = User(email=email, display_name=display_name)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _set_time(monkeypatch: pytest.MonkeyPatch, dt: datetime) -> None:
    monkeypatch.setattr(leaderboard_service, "now_utc", lambda: dt)
    monkeypatch.setattr(time_utils, "now_utc", lambda: dt)


def test_create_leaderboard_generates_join_code(client, test_engine):
    creator = _create_user(test_engine, "creator@example.com", "Creator")
    response = client.post(
        "/leaderboards/",
        json={"name": "Test Board", "course_id": "CS101"},
        headers={"X-User-Id": str(creator.id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["join_code"]
    assert len(data["join_code"]) == 7
    assert data["join_code"].isupper()


def test_join_leaderboard_twice_conflict(client, test_engine):
    creator = _create_user(test_engine, "creator@example.com")
    joiner = _create_user(test_engine, "joiner@example.com")

    create_resp = client.post(
        "/leaderboards/",
        json={"name": "Join Board"},
        headers={"X-User-Id": str(creator.id)},
    )
    code = create_resp.json()["join_code"]

    join_resp = client.post(
        "/leaderboards/join",
        json={"code": code.lower()},
        headers={"X-User-Id": str(joiner.id)},
    )
    assert join_resp.status_code == 200

    dup_resp = client.post(
        "/leaderboards/join",
        json={"code": code},
        headers={"X-User-Id": str(joiner.id)},
    )
    assert dup_resp.status_code == 409


def test_award_points_default_and_custom(client, test_engine):
    creator = _create_user(test_engine, "creator@example.com")
    member = _create_user(test_engine, "member@example.com")

    create_resp = client.post(
        "/leaderboards/",
        json={"name": "Points Board"},
        headers={"X-User-Id": str(creator.id)},
    )
    board_id = create_resp.json()["id"]
    code = create_resp.json()["join_code"]

    client.post(
        "/leaderboards/join",
        json={"code": code},
        headers={"X-User-Id": str(member.id)},
    )

    default_event = client.post(
        f"/leaderboards/{board_id}/award",
        json={"event_type": "task_completed"},
        headers={"X-User-Id": str(member.id)},
    )
    assert default_event.status_code == 201
    assert default_event.json()["points"] == DEFAULT_EVENT_POINTS["task_completed"]

    custom_event = client.post(
        f"/leaderboards/{board_id}/award",
        params={"user_id": member.id},
        json={"event_type": "bonus_swarm", "points": 7},
        headers={"X-User-Id": str(creator.id)},
    )
    assert custom_event.status_code == 201
    assert custom_event.json()["points"] == 7

    standings = client.get(
        f"/leaderboards/{board_id}",
        headers={"X-User-Id": str(member.id)},
    )
    assert standings.status_code == 200
    payload = standings.json()
    member_row = next(row for row in payload["members"] if row["user_id"] == member.id)
    assert member_row["weekly_points"] == DEFAULT_EVENT_POINTS["task_completed"] + 7
    assert member_row["total_points"] == DEFAULT_EVENT_POINTS["task_completed"] + 7


def test_standings_sorting_and_tie_breakers(client, test_engine, monkeypatch):
    creator = _create_user(test_engine, "creator@example.com")
    user_b = _create_user(test_engine, "b@example.com")
    user_c = _create_user(test_engine, "c@example.com")

    create_resp = client.post(
        "/leaderboards/",
        json={"name": "Sort Board"},
        headers={"X-User-Id": str(creator.id)},
    )
    board_id = create_resp.json()["id"]
    code = create_resp.json()["join_code"]

    client.post(
        "/leaderboards/join",
        json={"code": code},
        headers={"X-User-Id": str(user_b.id)},
    )
    client.post(
        "/leaderboards/join",
        json={"code": code},
        headers={"X-User-Id": str(user_c.id)},
    )

    today = datetime(2025, 1, 6, 10, tzinfo=timezone.utc)
    _set_time(monkeypatch, today)
    client.post(
        f"/leaderboards/{board_id}/award",
        json={"event_type": "task_completed"},
        headers={"X-User-Id": str(user_b.id)},
    )
    client.post(
        f"/leaderboards/{board_id}/award",
        json={"event_type": "task_completed"},
        headers={"X-User-Id": str(user_c.id)},
    )

    client.post(
        f"/leaderboards/{board_id}/award",
        json={"event_type": "task_completed"},
        headers={"X-User-Id": str(creator.id)},
    )
    client.post(
        f"/leaderboards/{board_id}/award",
        json={"event_type": "task_completed"},
        headers={"X-User-Id": str(creator.id)},
    )

    prior_week = today - timedelta(days=7)
    _set_time(monkeypatch, prior_week)
    client.post(
        f"/leaderboards/{board_id}/award",
        json={"event_type": "deadline_beaten"},
        headers={"X-User-Id": str(user_b.id)},
    )

    _set_time(monkeypatch, today)
    standings = client.get(
        f"/leaderboards/{board_id}",
        headers={"X-User-Id": str(creator.id)},
    )
    assert standings.status_code == 200
    members = standings.json()["members"]
    assert members[0]["user_id"] == creator.id
    assert members[1]["user_id"] == user_b.id
    assert members[2]["user_id"] == user_c.id


def test_consent_controls_display_name(client, test_engine):
    creator = _create_user(test_engine, "creator@example.com")
    member = _create_user(test_engine, "member@example.com", "Member Name")

    board = client.post(
        "/leaderboards/",
        json={"name": "Consent Board"},
        headers={"X-User-Id": str(creator.id)},
    ).json()

    client.post(
        "/leaderboards/join",
        json={"code": board["join_code"]},
        headers={"X-User-Id": str(member.id)},
    )

    standings = client.get(
        f"/leaderboards/{board['id']}",
        headers={"X-User-Id": str(member.id)},
    ).json()
    member_row = next(row for row in standings["members"] if row["user_id"] == member.id)
    assert member_row["display_name"] is None

    consent_true = client.post(
        f"/leaderboards/{board['id']}/consent",
        json={"display_consent": True},
        headers={"X-User-Id": str(member.id)},
    )
    assert consent_true.json()["display_name"] == "Member Name"

    consent_false = client.post(
        f"/leaderboards/{board['id']}/consent",
        json={"display_consent": False},
        headers={"X-User-Id": str(member.id)},
    )
    assert consent_false.json()["display_name"] is None


def test_daily_streak_counts_consecutive_days(client, test_engine, monkeypatch):
    creator = _create_user(test_engine, "creator@example.com")
    member = _create_user(test_engine, "member@example.com")

    board = client.post(
        "/leaderboards/",
        json={"name": "Streak Board"},
        headers={"X-User-Id": str(creator.id)},
    ).json()
    client.post(
        "/leaderboards/join",
        json={"code": board["join_code"]},
        headers={"X-User-Id": str(member.id)},
    )

    base_day = datetime(2025, 1, 6, 8, tzinfo=timezone.utc)
    for offset in range(3):
        _set_time(monkeypatch, base_day + timedelta(days=offset))
        client.post(
            f"/leaderboards/{board['id']}/award",
            json={"event_type": "task_completed"},
            headers={"X-User-Id": str(member.id)},
        )

    _set_time(monkeypatch, base_day + timedelta(days=2))
    standings = client.get(
        f"/leaderboards/{board['id']}",
        headers={"X-User-Id": str(member.id)},
    ).json()
    member_row = next(row for row in standings["members"] if row["user_id"] == member.id)
    assert member_row["streak_days"] == 3
# >>> LEADERBOARD END TESTS
