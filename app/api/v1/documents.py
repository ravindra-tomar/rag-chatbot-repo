from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.schemas.document import (
    ChunkPreview,
    DocumentDeleteResponse,
    DocumentIngestResponse,
    DocumentListResponse,
    DocumentSummary,
    SearchHit,
    SearchRequest,
    SearchResponse,
)
from app.services.embedding_service import embed_query
from app.services.ingest_service import delete_document, ingest_upload, list_documents
from app.services.vector_store import search_chunks
from app.api.v1.auth import get_current_user
from app.db.database import get_db
from app.db.models import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PDF/TXT upload → extract → chunk → embed → Chroma store.
    """
    try:
        meta = await ingest_upload(file, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")

    previews = [
        ChunkPreview(
            chunk_index=i,
            text=(chunk[:120] + ("..." if len(chunk) > 120 else "")),
            char_count=len(chunk),
        )
        for i, chunk in enumerate(meta["chunks"])
    ]

    return DocumentIngestResponse(
        doc_id=meta["doc_id"],
        filename=meta["filename"],
        char_count=meta["char_count"],
        chunk_count=meta["chunk_count"],
        vectors_stored=meta["vectors_stored"],
        chunks=previews,
    )


@router.get("", response_model=DocumentListResponse)
def get_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Saare ingested documents ki list."""
    docs = list_documents(db, current_user.id)
    return DocumentListResponse(
        count=len(docs),
        documents=[DocumentSummary(**d) for d in docs],
    )


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
def remove_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Document + uske vectors delete karo."""
    try:
        result = delete_document(doc_id, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")
    return DocumentDeleteResponse(**result)


@router.post("/search", response_model=SearchResponse)
def search_documents(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Question embed karke Chroma se related chunks nikaalta hai.
    """
    try:
        query_vec = embed_query(payload.query)
        hits = search_chunks(query_vec, top_k=payload.top_k, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Search failed: {e}")

    return SearchResponse(
        query=payload.query,
        hit_count=len(hits),
        hits=[SearchHit(**hit) for hit in hits],
    )
