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