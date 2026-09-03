import json
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.ml.chunker import chunk_text
from app.ml.loader import extract_text
from app.services.embedding_service import embed_texts
from app.services.vector_store import add_chunks, delete_doc

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


def _upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _meta_path(doc_id: str) -> Path:
    return _upload_dir() / f"{doc_id}.meta.json"


def list_documents() -> list[dict]:
    """Upload folder me saved documents ki list."""
    docs: list[dict] = []
    for meta_file in sorted(_upload_dir().glob("*.meta.json")):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        docs.append(
            {
                "doc_id": meta.get("doc_id"),
                "filename": meta.get("filename"),
                "char_count": meta.get("char_count", 0),
                "chunk_count": meta.get("chunk_count", 0),
                "vectors_stored": meta.get("vectors_stored", 0),
            }
        )
    return docs


def delete_document(doc_id: str) -> dict:
    """
    Document control:
    1) Chroma se vectors hatao
    2) saved file hatao
    3) meta.json hatao
    """
    meta_file = _meta_path(doc_id)
    if not meta_file.exists():
        raise ValueError(f"Document not found: {doc_id}")

    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    filename = meta.get("filename")
    saved_path = Path(meta.get("saved_path") or "")

    delete_doc(doc_id)

    if saved_path.exists():
        saved_path.unlink()

    meta_file.unlink()

    return {"doc_id": doc_id, "filename": filename, "deleted": True}


async def ingest_upload(file: UploadFile) -> dict:
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

    content = await file.read()
    if not content:
        raise ValueError("Empty file nahi chalega.")

    saved_path.write_bytes(content)

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

    return meta
