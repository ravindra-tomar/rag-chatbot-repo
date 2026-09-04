import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def credentials():
    return {
        "email": f"{uuid.uuid4().hex}@example.com",
        "password": "password123",
    }


def test_register_and_login_return_access_tokens():
    payload = credentials()
    register_response = client.post("/api/v1/auth/register", json=payload)

    assert register_response.status_code == 201
    assert register_response.json()["token_type"] == "bearer"
    assert register_response.json()["access_token"]

    login_response = client.post("/api/v1/auth/login", json=payload)

    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


def test_duplicate_registration_is_rejected():
    payload = credentials()
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_swagger_token_endpoint_accepts_form_credentials():
    payload = credentials()
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post(
        "/api/v1/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_protected_document_list_requires_token():
    response = client.get("/api/v1/documents")

    assert response.status_code == 401
