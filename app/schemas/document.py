from pydantic import BaseModel, Field


class ChunkPreview(BaseModel):
    chunk_index: int
    text: str = Field(..., description="Chunk ka pehla hissa (preview)")
    char_count: int


class DocumentIngestResponse(BaseModel):
    doc_id: str
    filename: str
    char_count: int
    chunk_count: int
    vectors_stored: int
    chunks: list[ChunkPreview]
    status: str = "created"
    duplicate: bool = False


class MultiDocumentIngestResponse(BaseModel):
    count: int
    documents: list[DocumentIngestResponse]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)


class SearchHit(BaseModel):
    text: str
    doc_id: str | None = None
    filename: str | None = None
    chunk_index: int | None = None
    distance: float | None = None


class SearchResponse(BaseModel):
    query: str
    hit_count: int
    hits: list[SearchHit]


class DocumentSummary(BaseModel):
    doc_id: str | None = None
    filename: str | None = None
    char_count: int = 0
    chunk_count: int = 0
    vectors_stored: int = 0


class DocumentListResponse(BaseModel):
    count: int
    documents: list[DocumentSummary]


class DocumentDeleteResponse(BaseModel):
    doc_id: str
    filename: str | None = None
    deleted: bool
