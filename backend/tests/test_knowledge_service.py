import pytest

from backend.app.knowledge.service import KnowledgeService


def test_calculate_content_hash():
    content = "Database backup verification"

    result = KnowledgeService.calculate_content_hash(
        content
    )

    assert len(result) == 64
    assert isinstance(result, str)


def test_calculate_content_hash_rejects_empty_content():
    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        KnowledgeService.calculate_content_hash("")


def test_calculate_content_hash_rejects_whitespace_content():
    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        KnowledgeService.calculate_content_hash("   ")


@pytest.mark.asyncio
async def test_ingest_document_rejects_empty_title():
    service = KnowledgeService()

    with pytest.raises(
        ValueError,
        match="Document title cannot be empty.",
    ):
        await service.ingest_document(
            title="",
            content="Database backup verification",
            source_type="sop",
        )


@pytest.mark.asyncio
async def test_ingest_document_rejects_empty_content():
    service = KnowledgeService()

    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        await service.ingest_document(
            title="Database Backup",
            content="",
            source_type="sop",
        )


@pytest.mark.asyncio
async def test_ingest_document_skips_unchanged_document(
    monkeypatch,
):
    service = KnowledgeService()

    content = "Database backup verification"
    content_hash = service.calculate_content_hash(
        content
    )

    existing_document = {
        "id": 123,
        "title": "Database Backup",
        "content": content,
        "source_type": "sop",
        "source_reference": "test/database_backup.md",
        "metadata": {},
        "content_hash": content_hash,
    }

    def mock_get_document_by_source_reference(
        source_reference,
    ):
        assert source_reference == "test/database_backup.md"
        return existing_document

    async def fail_if_embedding_called(text):
        raise AssertionError(
            "Embedding should not be generated for unchanged content."
        )

    monkeypatch.setattr(
        service.repository,
        "get_document_by_source_reference",
        mock_get_document_by_source_reference,
    )

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        fail_if_embedding_called,
    )

    document_id = await service.ingest_document(
        title="Database Backup",
        content=content,
        source_type="sop",
        source_reference="test/database_backup.md",
    )

    assert document_id == 123