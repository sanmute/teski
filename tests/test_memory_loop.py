# >>> MEMORY START
from fastapi.testclient import TestClient

from backend.main import app


def test_memory_plan_smoke():
    client = TestClient(app)
    response = client.post("/api/v1/memory/plan", json={"count": 2, "horizon_minutes": 60})
    assert response.status_code in (200, 401, 403)


def test_memory_log_smoke():
    client = TestClient(app)
    response = client.post("/api/v1/memory/log", json={"error_type": "recall"})
    assert response.status_code in (200, 401, 403)
# <<< MEMORY END
