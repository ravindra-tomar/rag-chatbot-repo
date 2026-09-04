from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_headers():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "api-tests@example.com", "password": "password123"},
    )
    if response.status_code == 409:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "api-tests@example.com", "password": "password123"},
        )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_validates_empty_message():
    response = client.post(
        "/api/v1/chat", json={"message": ""}, headers=auth_headers()
    )

    assert response.status_code == 422


def test_search_validates_top_k():
    response = client.post(
        "/api/v1/documents/search",
        json={"query": "leave policy", "top_k": 11},
        headers=auth_headers(),
    )

    assert response.status_code == 422


def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.docx", b"text", "application/octet-stream")},
        headers=auth_headers(),
    )

    assert response.status_code == 400
    assert "Only .pdf and .txt files allowed" in response.json()["detail"]
