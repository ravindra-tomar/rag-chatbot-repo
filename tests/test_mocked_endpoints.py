from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_headers(email="mock-tests@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    if response.status_code == 409:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def fake_ingest_upload(file, user_id, db):
    return {
        "doc_id": "doc-123",
        "filename": file.filename,
        "char_count": 11,
        "chunk_count": 1,
        "vectors_stored": 1,
        "chunks": ["hello policy"],
    }


def fake_answer_with_rag(
    message, top_k=None, session_id=None, user_id=None, db=None
):
    return {
        "session_id": session_id or "session-123",
        "answer": "WFH is allowed.",
        "used_context": True,
        "sources": [
            {
                "filename": "policy.txt",
                "doc_id": "doc-123",
                "chunk_index": 0,
                "distance": 0.1,
                "preview": "WFH is allowed.",
            }
        ],
    }


def test_upload_endpoint_with_mocked_ingestion(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.documents.ingest_upload", fake_ingest_upload
    )

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("policy.txt", b"hello policy", "text/plain")},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["doc_id"] == "doc-123"
    assert response.json()["vectors_stored"] == 1


def test_multiple_upload_endpoint_with_mocked_ingestion(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.documents.ingest_upload", fake_ingest_upload
    )

    response = client.post(
        "/api/v1/documents/upload-multiple",
        files=[
            ("files", ("policy-a.txt", b"policy a", "text/plain")),
            ("files", ("policy-b.txt", b"policy b", "text/plain")),
        ],
        headers=auth_headers("multiple-upload-tests@example.com"),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert [item["filename"] for item in response.json()["documents"]] == [
        "policy-a.txt",
        "policy-b.txt",
    ]


def test_chat_endpoint_with_mocked_rag(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.chat.answer_with_rag", fake_answer_with_rag
    )

    response = client.post(
        "/api/v1/chat",
        json={"message": "WFH kitne din allowed hain?"},
        headers=auth_headers("chat-tests@example.com"),
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "WFH is allowed."
    assert response.json()["used_context"] is True
    assert response.json()["sources"][0]["filename"] == "policy.txt"
