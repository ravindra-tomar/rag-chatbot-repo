from google import genai
from google.genai import types

from app.core.config import settings


def get_chat_answer(message: str) -> str:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY missing hai. .env me key daalo.")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            headers={"x-goog-api-key": settings.GEMINI_API_KEY},
        ),
    )

    response = client.models.generate_content(
        model=settings.CHAT_MODEL,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction="You are a helpful assistant. Keep answers short and clear.",
        ),
    )

    return (response.text or "").strip()
