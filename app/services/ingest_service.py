import json
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.chunker import chunk_text
from app.ml.loader import extract_text
from app.services.embedding_service import embed_texts
from app.services.vector_store import add_chunks, delete_doc
from app.db.models import Document

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


def _upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _meta_path(doc_id: str) -> Path:
    return _upload_dir() / f"{doc_id}.meta.json"


def list_documents(db: Session, user_id: int) -> list[dict]:
    """Current user ke documents ki list."""
    docs = db.scalars(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at)
    ).all()
    return [
        {
            "doc_id": doc.id,
            "filename": doc.filename,
            "char_count": doc.char_count,
            "chunk_count": doc.chunk_count,
            "vectors_stored": doc.vectors_stored,
        }
        for doc in docs
    ]


def delete_document(doc_id: str, user_id: int, db: Session) -> dict:
    """
    Document control:
    1) Chroma se vectors hatao
    2) saved file hatao
    3) meta.json hatao
    """
    document = db.scalar(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )
    if not document:
        raise ValueError(f"Document not found: {doc_id}")

    meta_file = _meta_path(doc_id)
    filename = document.filename
    saved_path = Path(document.saved_path)

    delete_doc(doc_id, user_id=user_id)

    if saved_path.exists():
        saved_path.unlink()

    if meta_file.exists():
        meta_file.unlink()

    db.delete(document)
    db.commit()

    return {"doc_id": doc_id, "filename": filename, "deleted": True}


async def ingest_upload(file: UploadFile, user_id: int, db: Session) -> dict:
    """
    Phase 3 + 4 pipeline:
    1) file save
    2) text extract
    3) chunk
    4) embed chunks
    5) Chroma me store
    6) metadata save
    """
    if not file.filename:
        raise ValueError("Filename missing hai.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .pdf and .txt files allowed.")

    doc_id = uuid.uuid4().hex
    saved_path = _upload_dir() / f"{doc_id}{suffix}"

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read(max_size + 1)
    if not content:
        raise ValueError("Empty file nahi chalega.")
    if len(content) > max_size:
        raise ValueError(f"File size {settings.MAX_UPLOAD_SIZE_MB} MB se zyada nahi ho sakti.")

    saved_path.write_bytes(content)
    try:
        text = extract_text(saved_path)
        if not text:
            raise ValueError("File se text nahi nikla. Scanned PDF ho sakti hai.")

        chunks = chunk_text(
            text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )
        if not chunks:
            raise ValueError("Chunks empty hain.")

        embeddings = embed_texts(chunks, task_type="RETRIEVAL_DOCUMENT")
        stored = add_chunks(
            doc_id=doc_id,
            filename=file.filename,
            user_id=user_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        meta = {
            "doc_id": doc_id,
            "filename": file.filename,
            "saved_path": str(saved_path),
            "char_count": len(text),
            "chunk_count": len(chunks),
            "vectors_stored": stored,
            "chunks": chunks,
        }
        _meta_path(doc_id).write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        db.add(
            Document(
                id=doc_id,
                user_id=user_id,
                filename=file.filename,
                saved_path=str(saved_path),
                char_count=len(text),
                chunk_count=len(chunks),
                vectors_stored=stored,
            )
        )
        db.commit()
        return meta
    except Exception:
        delete_doc(doc_id, user_id=user_id)
        if saved_path.exists():
            saved_path.unlink()
        if _meta_path(doc_id).exists():
            _meta_path(doc_id).unlink()
        db.rollback()
        raise
