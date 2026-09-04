from pathlib import Path
from typing import Any

import chromadb

from app.core.config import settings

_client: Any = None
_collection: Any = None


def get_collection():
    """Chroma collection lazy-load — app start pe heavy init avoid."""
    global _client, _collection
    if _collection is not None:
        return _collection

    path = Path(settings.CHROMA_PATH)
    path.mkdir(parents=True, exist_ok=True)

    _client = chromadb.PersistentClient(path=str(path))
    _collection = _client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def add_chunks(
    *,
    doc_id: str,
    filename: str,
    user_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
) -> int:
    """Chunks + vectors Chroma me save."""
    if len(chunks) != len(embeddings):
        raise ValueError("chunks aur embeddings ki length same honi chahiye.")

    if not chunks:
        return 0

    collection = get_collection()
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "user_id": user_id,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def search_chunks(
    query_embedding: list[float], top_k: int | None = None, user_id: int | None = None
) -> list[dict]:
    """Query vector se sabse close chunks nikaalo."""
    k = top_k or settings.TOP_K
    collection = get_collection()

    if collection.count() == 0:
        return []

    where = {"user_id": user_id} if user_id is not None else None
    total_count = collection.count()
    if total_count == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, total_count),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    hits: list[dict] = []
    for doc, meta, distance in zip(docs, metas, distances):
        hits.append(
            {
                "text": doc,
                "doc_id": meta.get("doc_id"),
                "filename": meta.get("filename"),
                "chunk_index": meta.get("chunk_index"),
                "distance": distance,
            }
        )
    return hits


def delete_doc(doc_id: str, user_id: int | None = None) -> None:
    """Ek document ke saare chunks hatao."""
    collection = get_collection()
    where = {"doc_id": doc_id}
    if user_id is not None:
        where = {"$and": [{"doc_id": doc_id}, {"user_id": user_id}]}
    collection.delete(where=where)
