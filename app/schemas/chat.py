from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User ka message")
    top_k: int = Field(default=4, ge=1, le=10, description="Kitne chunks retrieve karne hain")
    session_id: str | None = Field(
        default=None,
        description="Optional session id for chat memory continuity",
    )


class ChatSource(BaseModel):
    filename: str | None = None
    doc_id: str | None = None
    chunk_index: int | None = None
    distance: float | None = None
    preview: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    used_context: bool
    sources: list[ChatSource] = []
