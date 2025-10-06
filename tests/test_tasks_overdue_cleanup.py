# >>> DFE START
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

import backend.models  # noqa: F401 ensure tables registered
from backend.db import get_session
from backend.main import app
from backend.models import SourceEnum, StatusEnum, Task
from backend.settings import DEFAULT_TIMEZONE


def test_overdue_tasks_expunged_after_36_hours():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)

    overdue_due = datetime.now(DEFAULT_TIMEZONE) - timedelta(hours=40)
    fresh_due = datetime.now(DEFAULT_TIMEZONE) - timedelta(hours=10)

    with Session(engine) as session:
        session.add(
            Task(
                id="stale",
                source=SourceEnum.mock,
                title="Stale Task",
                due_iso=overdue_due,
                status=StatusEnum.overdue,
            )
        )
        session.add(
            Task(
                id="recent",
                source=SourceEnum.mock,
                title="Recent Overdue Task",
                due_iso=fresh_due,
                status=StatusEnum.overdue,
            )
        )
        session.commit()

    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    ids = {task["id"] for task in tasks}
    assert "recent" in ids
    assert "stale" not in ids

    with Session(engine) as session:
        assert session.get(Task, "stale") is None
        assert session.get(Task, "recent") is not None

    app.dependency_overrides.clear()
# <<< DFE END
