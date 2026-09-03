from google import genai
from google.genai import types

from app.core.config import settings


def _client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY missing hai. .env me key daalo.")
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            headers={"x-goog-api-key": settings.GEMINI_API_KEY},
        ),
    )


def embed_texts(texts: list[str], *, task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Text list → embedding vectors.

    task_type:
      - RETRIEVAL_DOCUMENT → jab chunks store karte ho
      - RETRIEVAL_QUERY → jab user question embed karte ho
    """
    if not texts:
        return []

    client = _client()
    response = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )

    vectors: list[list[float]] = []
    for item in response.embeddings or []:
        if item.values is None:
            raise RuntimeError("Embedding values missing from Gemini response.")
        vectors.append(list(item.values))

    if len(vectors) != len(texts):
        raise RuntimeError("Embedding count text count se match nahi karta.")

    return vectors


def embed_query(query: str) -> list[float]:
    """User question ke liye single embedding."""
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
