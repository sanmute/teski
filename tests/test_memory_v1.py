# >>> MEMORY V1 START
from fastapi.testclient import TestClient

from backend.main import app


def test_memory_v1_routes_exist():
    client = TestClient(app)
    response = client.post("/api/v1/memory/log/v1", json={"error_type": "mistake", "detail": {}})
    assert response.status_code in (200, 401, 403)

    response = client.post("/api/v1/memory/review/build", json={"max_new": 2, "horizon_minutes": 60})
    assert response.status_code in (200, 401, 403)

    response = client.get("/api/v1/memory/review/next?count=2")
    assert response.status_code in (200, 401, 403)
# <<< MEMORY V1 END
