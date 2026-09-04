from app.ml.chunker import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("   ") == []


def test_short_text_stays_in_one_chunk():
    assert chunk_text("hello world", chunk_size=20, overlap=5) == ["hello world"]


def test_long_text_uses_overlap():
    chunks = chunk_text("a" * 1700, chunk_size=800, overlap=150)

    assert len(chunks) == 3
    assert chunks[0][-150:] == chunks[1][:150]
    assert chunks[1][-150:] == chunks[2][:150]
