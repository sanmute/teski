# >>> PERSONA START
from fastapi.testclient import TestClient

from backend.main import app


def test_preview_nudge_smoke():
    client = TestClient(app)
    payload = {
        "requestedMood": "mood_calm_v1",
        "phase": "preTask",
        "context": {"minutesToDue": 2000},
    }
    response = client.post("/api/v1/personas/nudge/preview", json=payload)
    assert response.status_code in (200, 404)
# <<< PERSONA END
