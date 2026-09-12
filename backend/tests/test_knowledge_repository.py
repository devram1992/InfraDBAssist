import pytest

from backend.app.database.repository import KnowledgeRepository


def test_update_chunk_embedding_rejects_invalid_dimension():
    repository = KnowledgeRepository()

    embedding = [0.1, 0.2, 0.3]

    with pytest.raises(
        ValueError,
        match="Expected 1024 dimensions, received 3.",
    ):
        repository.update_chunk_embedding(
            chunk_id=1,
            embedding=embedding,
        )


def test_update_embedding_rejects_invalid_dimension():
    repository = KnowledgeRepository()

    embedding = [0.1, 0.2, 0.3]

    with pytest.raises(
        ValueError,
        match="Expected 1024 dimensions, received 3.",
    ):
        repository.update_embedding(
            document_id=1,
            embedding=embedding,
        )


def test_create_chunk_rejects_negative_chunk_index():
    repository = KnowledgeRepository()

    with pytest.raises(
        ValueError,
        match="Chunk index cannot be negative.",
    ):
        repository.create_chunk(
            document_id=1,
            chunk_index=-1,
            content="Database backup verification",
        )


def test_create_chunk_rejects_empty_content():
    repository = KnowledgeRepository()

    with pytest.raises(
        ValueError,
        match="Chunk content cannot be empty.",
    ):
        repository.create_chunk(
            document_id=1,
            chunk_index=0,
            content="",
        )


def test_create_chunk_rejects_whitespace_content():
    repository = KnowledgeRepository()

    with pytest.raises(
        ValueError,
        match="Chunk content cannot be empty.",
    ):
        repository.create_chunk(
            document_id=1,
            chunk_index=0,
            content="   ",
        )


def test_replace_document_rolls_back_on_chunk_insert_failure():
    repository = KnowledgeRepository()

    document_id = repository.create_document(
        title="Original Document",
        content="Original content",
        source_type="sop",
        source_reference="test/rollback.md",
        metadata={},
    )

    original_chunk = {
        "chunk_index": 0,
        "content": "Original chunk",
        "embedding": [0.1] * 1024,
        "metadata": {},
    }

    repository.replace_document_chunks(
        document_id=document_id,
        chunks=[original_chunk],
    )

    updated_chunks = [
        {
            "chunk_index": 0,
            "content": "Updated chunk",
            "embedding": [0.2] * 1024,
            "metadata": {},
        },
        {
            "chunk_index": 0,
            "content": "Duplicate chunk index",
            "embedding": [0.3] * 1024,
            "metadata": {},
        },
    ]

    with pytest.raises(Exception):
        repository.replace_document(
            document_id=document_id,
            title="Updated Document",
            content="Updated content",
            source_type="sop",
            metadata={},
            content_hash="a" * 64,
            chunks=updated_chunks,
        )

    document = repository.get_document(document_id)

    assert document["title"] == "Original Document"
    assert document["content"] == "Original content"

    chunks = repository.search_similar_chunks(
        embedding=[0.1] * 1024,
        limit=10,
    )

    document_chunks = [
        chunk
        for chunk in chunks
        if chunk["document_id"] == document_id
    ]

    assert len(document_chunks) == 1
    assert document_chunks[0]["content"] == "Original chunk"

    repository.delete_document(document_id)