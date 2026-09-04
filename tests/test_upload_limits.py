from fastapi.testclient import TestClient
import uuid

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_upload_rejects_files_over_configured_limit(monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    auth_response = client.post(
        "/api/v1/auth/register",
        json={"email": f"{uuid.uuid4().hex}@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large.txt", b"x" * (1024 * 1024 + 1), "text/plain")},
        headers={
            "Authorization": f"Bearer {auth_response.json()['access_token']}",
        },
    )

    assert response.status_code == 400
    assert "1 MB" in response.json()["detail"]