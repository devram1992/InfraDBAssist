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
    new_content = (
        "Database backup verification and "
        "archive log validation"
    )

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
    assert len(
        replace_request["chunks"][0]["embedding"]
    ) == 1024


@pytest.mark.asyncio
async def test_ingest_document_cleans_up_new_document_on_failure(
    monkeypatch,
):
    service = KnowledgeService()

    created_document_id = 789

    def mock_create_document(**kwargs):
        return created_document_id

    def mock_update_content_hash(
        document_id,
        content_hash,
    ):
        assert document_id == created_document_id

    def fail_replace_document_chunks(
        document_id,
        chunks,
    ):
        raise RuntimeError(
            "Failed to insert knowledge chunks."
        )

    deleted_document_ids = []

    def mock_delete_document(document_id):
        deleted_document_ids.append(
            document_id
        )

    async def mock_embed(text):
        return [0.1] * 1024

    monkeypatch.setattr(
        service.repository,
        "get_document_by_source_reference",
        lambda source_reference: None,
    )

    monkeypatch.setattr(
        service.repository,
        "create_document",
        mock_create_document,
    )

    monkeypatch.setattr(
        service.repository,
        "update_content_hash",
        mock_update_content_hash,
    )

    monkeypatch.setattr(
        service.repository,
        "replace_document_chunks",
        fail_replace_document_chunks,
    )

    monkeypatch.setattr(
        service.repository,
        "delete_document",
        mock_delete_document,
    )

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        mock_embed,
    )

    with pytest.raises(
        RuntimeError,
        match="Failed to insert knowledge chunks.",
    ):
        await service.ingest_document(
            title="Database Backup",
            content="Database backup verification",
            source_type="sop",
            source_reference="test/database_backup.md",
        )

    assert deleted_document_ids == [
        created_document_id
    ]