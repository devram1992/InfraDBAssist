import pytest

from backend.app.knowledge.chunker import DocumentChunker


def test_chunker_rejects_invalid_chunk_size():
    with pytest.raises(
        ValueError,
        match="Chunk size must be greater than zero.",
    ):
        DocumentChunker(chunk_size=0)


def test_chunker_rejects_negative_overlap():
    with pytest.raises(
        ValueError,
        match="Chunk overlap cannot be negative.",
    ):
        DocumentChunker(
            chunk_size=100,
            chunk_overlap=-1,
        )


def test_chunker_rejects_overlap_equal_to_chunk_size():
    with pytest.raises(
        ValueError,
        match="Chunk overlap must be smaller than chunk size.",
    ):
        DocumentChunker(
            chunk_size=100,
            chunk_overlap=100,
        )


def test_chunker_rejects_overlap_greater_than_chunk_size():
    with pytest.raises(
        ValueError,
        match="Chunk overlap must be smaller than chunk size.",
    ):
        DocumentChunker(
            chunk_size=100,
            chunk_overlap=101,
        )


def test_chunker_rejects_empty_content():
    chunker = DocumentChunker()

    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        chunker.split("")


def test_chunker_rejects_whitespace_content():
    chunker = DocumentChunker()

    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        chunker.split("   ")


def test_chunker_returns_single_chunk_for_small_document():
    chunker = DocumentChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    content = "Database backup verification"

    chunks = chunker.split(content)

    assert chunks == [
        content
    ]


def test_chunker_returns_single_chunk_at_exact_chunk_size():
    chunker = DocumentChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    content = "ABCDEFGHIJ"

    chunks = chunker.split(content)

    assert chunks == [
        content
    ]


def test_chunker_creates_overlapping_chunks():
    chunker = DocumentChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    content = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    chunks = chunker.split(content)

    assert chunks == [
        "ABCDEFGHIJ",
        "IJKLMNOPQR",
        "QRSTUVWXYZ",
    ]


def test_chunker_strips_document_whitespace():
    chunker = DocumentChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = chunker.split(
        "   Database backup verification   "
    )

    assert chunks == [
        "Database backup verification"
    ]