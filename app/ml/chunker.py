def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """
    Bade text ko chhote pieces me todta hai.

    Why: LLM/vector search ek baar me pura document handle nahi karte.
    Overlap: do chunks ke beech thoda common text — context tootna kam hota hai.
    """
    text = " ".join(text.split())
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap

    return chunks
