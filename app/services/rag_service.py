import uuid

from google import genai
from google.genai import types

from app.core.config import settings
from app.services.embedding_service import embed_query
from app.services.vector_store import search_chunks

SYSTEM_PROMPT = """You are a helpful RAG assistant.
Answer ONLY using the provided context from uploaded documents.
If the context is empty or does not contain the answer, say clearly that you don't know based on the documents.
Keep answers short and clear.
Do not invent facts outside the context."""

# Simple in-memory session store for chat continuity.
# Format: {session_id: [{"role": "user|assistant", "text": "..."}]}
SESSION_MEMORY: dict[str, list[dict[str, str]]] = {}
MAX_MEMORY_TURNS = 6


def _gemini_client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY missing hai. .env me key daalo.")
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            headers={"x-goog-api-key": settings.GEMINI_API_KEY},
        ),
    )


def _build_context(hits: list[dict]) -> str:
    if not hits:
        return ""
    parts: list[str] = []
    for i, hit in enumerate(hits, start=1):
        filename = hit.get("filename") or "unknown"
        chunk_index = hit.get("chunk_index")
        text = hit.get("text") or ""
        parts.append(f"[Source {i}] file={filename} chunk={chunk_index}\n{text}")
    return "\n\n".join(parts)


def _ensure_session(session_id: str | None) -> str:
    if session_id:
        SESSION_MEMORY.setdefault(session_id, [])
        return session_id
    new_session_id = uuid.uuid4().hex
    SESSION_MEMORY[new_session_id] = []
    return new_session_id


def _history_text(session_id: str) -> str:
    turns = SESSION_MEMORY.get(session_id, [])
    if not turns:
        return "(no previous chat history)"

    recent = turns[-(MAX_MEMORY_TURNS * 2) :]
    lines = [f"{turn['role']}: {turn['text']}" for turn in recent]
    return "\n".join(lines)


def _append_turn(session_id: str, role: str, text: str) -> None:
    SESSION_MEMORY.setdefault(session_id, []).append({"role": role, "text": text})


def answer_with_rag(
    question: str, top_k: int | None = None, session_id: str | None = None
) -> dict:
    """
    Phase 5 pipeline (+ basic memory):
    1) question embed
    2) Chroma se related chunks
    3) history + context + question → Gemini
    4) answer + sources + session_id
    """
    current_session = _ensure_session(session_id)

    query_vec = embed_query(question)
    hits = search_chunks(query_vec, top_k=top_k)
    context = _build_context(hits)
    history = _history_text(current_session)

    user_prompt = (
        f"Chat History:\n{history}\n\n"
        f"Context:\n{context if context else '(no documents found)'}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context. Use history only for conversation continuity."
    )

    client = _gemini_client()
    response = client.models.generate_content(
        model=settings.CHAT_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    answer = (response.text or "").strip()

    _append_turn(current_session, "user", question)
    _append_turn(current_session, "assistant", answer)

    sources = [
        {
            "filename": hit.get("filename"),
            "doc_id": hit.get("doc_id"),
            "chunk_index": hit.get("chunk_index"),
            "distance": hit.get("distance"),
            "preview": (hit.get("text") or "")[:160]
            + ("..." if len(hit.get("text") or "") > 160 else ""),
        }
        for hit in hits
    ]

    return {
        "answer": answer,
        "sources": sources,
        "used_context": bool(hits),
        "session_id": current_session,
    }
