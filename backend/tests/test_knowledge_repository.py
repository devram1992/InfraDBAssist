import pytest

from backend.app.database.repository import KnowledgeRepository


def test_update_chunk_embedding_rejects_invalid_dimension(
    monkeypatch,
):
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


def test_update_embedding_rejects_invalid_dimension(
    monkeypatch,
):
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