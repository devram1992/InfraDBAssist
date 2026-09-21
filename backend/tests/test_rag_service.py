import pytest

from backend.app.rag.service import RAGService


@pytest.mark.asyncio
async def test_rag_search_returns_similar_chunks(monkeypatch):
    service = RAGService()

    expected_embedding = [0.1] * 1024

    expected_results = [
        {
            "chunk_id": 1,
            "document_id": 10,
            "title": "database_backup",
            "source_type": "sop",
            "similarity": 0.91,
            "content": "Verify backup completion.",
        }
    ]

    captured = {}

    async def mock_embed(text):
        captured["question"] = text
        return expected_embedding

    def mock_search_similar_chunks(
        embedding,
        limit,
        similarity_threshold=None,
    ):
        captured["embedding"] = embedding
        captured["limit"] = limit
        captured["similarity_threshold"] = similarity_threshold

        return expected_results

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        mock_embed,
    )

    monkeypatch.setattr(
        service.repository,
        "search_similar_chunks",
        mock_search_similar_chunks,
    )

    result = await service.search(
        question="How do I verify database backups?",
        limit=5,
    )

    assert result == expected_results
    assert captured["question"] == (
        "How do I verify database backups?"
    )
    assert captured["embedding"] == expected_embedding
    assert captured["limit"] == 5
    assert captured["similarity_threshold"] == 0.60


@pytest.mark.asyncio
async def test_rag_search_uses_default_limit(monkeypatch):
    service = RAGService()

    captured = {}

    async def mock_embed(text):
        return [0.1] * 1024

    def mock_search_similar_chunks(
        embedding,
        limit,
        similarity_threshold=None,
    ):
        captured["limit"] = limit
        captured["similarity_threshold"] = similarity_threshold

        return []

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        mock_embed,
    )

    monkeypatch.setattr(
        service.repository,
        "search_similar_chunks",
        mock_search_similar_chunks,
    )

    result = await service.search(
        question="Oracle performance troubleshooting"
    )

    assert result == []
    assert captured["limit"] == 5
    assert captured["similarity_threshold"] == 0.60


@pytest.mark.asyncio
async def test_rag_search_passes_similarity_threshold(
    monkeypatch,
):
    service = RAGService()

    captured = {}

    async def mock_embed(text):
        return [0.1] * 1024

    def mock_search_similar_chunks(
        embedding,
        limit,
        similarity_threshold=None,
    ):
        captured["similarity_threshold"] = similarity_threshold
        return []

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        mock_embed,
    )

    monkeypatch.setattr(
        service.repository,
        "search_similar_chunks",
        mock_search_similar_chunks,
    )

    result = await service.search(
        question="Oracle performance troubleshooting",
        similarity_threshold=0.60,
    )

    assert result == []
    assert captured["similarity_threshold"] == 0.60


@pytest.mark.asyncio
async def test_rag_search_rejects_empty_question():
    service = RAGService()

    with pytest.raises(
        ValueError,
        match="Question cannot be empty.",
    ):
        await service.search("")


@pytest.mark.asyncio
async def test_rag_search_rejects_whitespace_question():
    service = RAGService()

    with pytest.raises(
        ValueError,
        match="Question cannot be empty.",
    ):
        await service.search("   ")


@pytest.mark.asyncio
async def test_rag_search_rejects_invalid_limit():
    service = RAGService()

    with pytest.raises(
        ValueError,
        match="Limit must be greater than zero.",
    ):
        await service.search(
            "Oracle performance troubleshooting",
            limit=0,
        )


@pytest.mark.asyncio
async def test_rag_search_rejects_invalid_similarity_threshold():
    service = RAGService()

    with pytest.raises(
        ValueError,
        match="Similarity threshold must be between 0 and 1.",
    ):
        await service.search(
            "Oracle performance troubleshooting",
            similarity_threshold=1.5,
        )


@pytest.mark.asyncio
async def test_rag_search_propagates_embedding_failure(
    monkeypatch,
):
    service = RAGService()

    async def fail_embed(text):
        raise RuntimeError(
            "Embedding service unavailable."
        )

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        fail_embed,
    )

    with pytest.raises(
        RuntimeError,
        match="Embedding service unavailable.",
    ):
        await service.search(
            "Oracle performance troubleshooting"
        )


@pytest.mark.asyncio
async def test_rag_search_propagates_repository_failure(
    monkeypatch,
):
    service = RAGService()

    async def mock_embed(text):
        return [0.1] * 1024

    def fail_search_similar_chunks(
        embedding,
        limit,
        similarity_threshold=None,
    ):
        raise RuntimeError(
            "Vector search unavailable."
        )

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        mock_embed,
    )

    monkeypatch.setattr(
        service.repository,
        "search_similar_chunks",
        fail_search_similar_chunks,
    )

    with pytest.raises(
        RuntimeError,
        match="Vector search unavailable.",
    ):
        await service.search(
            "Oracle performance troubleshooting"
        )
