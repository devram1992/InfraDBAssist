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


@pytest.mark.asyncio
async def test_ingest_document_updates_changed_document(
    monkeypatch,
):
    service = KnowledgeService()

    old_content = "Database backup verification"
    new_content = "Database backup verification and archive log validation"

    old_hash = service.calculate_content_hash(
        old_content
    )

    existing_document = {
        "id": 456,
        "title": "Database Backup",
        "content": old_content,
        "source_type": "sop",
        "source_reference": "test/database_backup.md",
        "metadata": {},
        "content_hash": old_hash,
    }

    captured = {}

    def mock_get_document_by_source_reference(
        source_reference,
    ):
        return existing_document

    async def mock_embed(text):
        captured["embedded_content"] = text
        return [0.1] * 1024

    def mock_replace_document(**kwargs):
        captured["replace_request"] = kwargs

    monkeypatch.setattr(
        service.repository,
        "get_document_by_source_reference",
        mock_get_document_by_source_reference,
    )

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        mock_embed,
    )

    monkeypatch.setattr(
        service.repository,
        "replace_document",
        mock_replace_document,
    )

    document_id = await service.ingest_document(
        title="Database Backup",
        content=new_content,
        source_type="sop",
        source_reference="test/database_backup.md",
    )

    assert document_id == 456

    assert captured["embedded_content"] == new_content

    replace_request = captured["replace_request"]

    assert replace_request["document_id"] == 456
    assert replace_request["content"] == new_content
    assert replace_request["source_type"] == "sop"
    assert replace_request["content_hash"] == (
        service.calculate_content_hash(new_content)
    )

    assert len(replace_request["chunks"]) == 1
    assert replace_request["chunks"][0]["content"] == new_content
    assert len(replace_request["chunks"][0]["embedding"]) == 1024