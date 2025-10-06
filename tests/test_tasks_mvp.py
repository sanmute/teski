# >>> DFE START
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

import backend.models  # noqa: F401 ensure base tables registered
import backend.models_dfe  # noqa: F401 ensure DFE tables registered
from backend.db import get_session
from backend.main import app
from backend.models import User


def _memory_engine():
    return create_engine("sqlite://", connect_args={"check_same_thread": False})


def test_template_instantiate_and_grade():
    engine = _memory_engine()
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)

    # create authenticated user recognised by dependency
    with Session(engine) as session:
        user = User(email="learner@example.com", display_name="Learner")
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    headers = {"X-User-Id": str(user_id)}
    template_payload = {
        "code": "phys.accel.01",
        "title": "Acceleration",
        "skill_key": "physics.kinematics.acceleration",
        "graph_version": "v1",
        "task_type": "numeric",
        "text_template": "A car accelerates from {{v0}} to {{v1}} in {{t}} s. Compute a.",
        "parameters": {"v0": [0, 5, 10], "v1": [15, 20, 25], "t": [3, 4, 5]},
        "constraints": {"expr": "v1 > v0 and t != 0"},
        "answer_spec": {"formula": "(v1 - v0)/t", "tolerance": 1e-6},
    }

    create_resp = client.post("/api/v1/tasks/templates", json=template_payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text

    inst_resp = client.post(f"/api/v1/tasks/instantiate/{template_payload['code']}", headers=headers)
    assert inst_resp.status_code == 200, inst_resp.text
    instance_payload = inst_resp.json()
    assert instance_payload["task_type"] == "numeric"
    assert instance_payload["template_code"] == template_payload["code"]

    params = instance_payload["params"]
    correct_answer = (params["v1"] - params["v0"]) / params["t"]

    submit_resp = client.post(
        f"/api/v1/tasks/submit/{instance_payload['instance_id']}",
        json={"answer": correct_answer, "latency_ms": 987},
        headers=headers,
    )
    assert submit_resp.status_code == 200, submit_resp.text
    submit_data = submit_resp.json()
    assert submit_data["correct"] is True
    assert 0.0 <= submit_data["mastery_after"] <= 1.0

    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)
    engine.dispose()
# <<< DFE END
