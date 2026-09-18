import hashlib

import pytest

from backend.app.knowledge.service import KnowledgeService


def test_calculate_content_hash():
    service = KnowledgeService()

    content = "Database backup verification"
    result = service.calculate_content_hash(content)

    assert len(result) == 64
    assert isinstance(result, str)
    assert result == hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def test_calculate_content_hash_rejects_empty_content():
    service = KnowledgeService()

    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        service.calculate_content_hash("")


def test_calculate_content_hash_rejects_whitespace_content():
    service = KnowledgeService()

    with pytest.raises(
        ValueError,
        match="Document content cannot be empty.",
    ):
        service.calculate_content_hash("   ")


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
            source_reference="knowledge/sop/database_backup.md",
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
            source_reference="knowledge/sop/database_backup.md",
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
        "content_hash": content_hash,
    }

    async def fail_embed(text):
        raise AssertionError(
            "Embedding should not be generated for unchanged content."
        )

    monkeypatch.setattr(
        service.repository,
        "get_document_by_source_reference",
        lambda source_reference: existing_document,
    )

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        fail_embed,
    )

    result = await service.ingest_document(
        title="Database Backup",
        content=content,
        source_type="sop",
        source_reference="knowledge/sop/database_backup.md",
    )

    assert result == 123


@pytest.mark.asyncio
async def test_ingest_document_updates_changed_document(
    monkeypatch,
):
    service = KnowledgeService()

    old_content = "Old database backup procedure."
    new_content = "New database backup procedure."

    existing_document = {
        "id": 456,
        "content_hash": service.calculate_content_hash(
            old_content
        ),
    }

    captured = {}

    async def mock_embed(text):
        captured["embedded_content"] = text
        return [0.1] * 1024

    def mock_replace_document(**kwargs):
        captured["replace_request"] = kwargs

    monkeypatch.setattr(
        service.repository,
        "get_document_by_source_reference",
        lambda source_reference: existing_document,
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

    result = await service.ingest_document(
        title="Database Backup",
        content=new_content,
        source_type="sop",
        source_reference="knowledge/sop/database_backup.md",
    )

    assert result == 456

    assert captured["embedded_content"] == new_content

    replace_request = captured["replace_request"]

    assert replace_request["document_id"] == 456
    assert replace_request["title"] == "Database Backup"
    assert replace_request["content"] == new_content
    assert replace_request["source_type"] == "sop"

    assert replace_request["content_hash"] == (
        service.calculate_content_hash(
            new_content
        )
    )


@pytest.mark.asyncio
async def test_ingest_document_uses_atomic_creation_for_new_document(
    monkeypatch,
):
    service = KnowledgeService()

    created_document_id = 789
    captured_request = {}

    def mock_create_document_with_chunks(**kwargs):
        captured_request.update(kwargs)
        return created_document_id

    async def mock_embed(text):
        return [0.1] * 1024

    monkeypatch.setattr(
        service.repository,
        "get_document_by_source_reference",
        lambda source_reference: None,
    )

    monkeypatch.setattr(
        service.repository,
        "create_document_with_chunks",
        mock_create_document_with_chunks,
    )

    monkeypatch.setattr(
        service.embedding_client,
        "embed",
        mock_embed,
    )

    result = await service.ingest_document(
        title="Database Backup",
        content="Database backup verification procedure.",
        source_type="sop",
        source_reference="knowledge/sop/database_backup.md",
        metadata={"category": "backup"},
    )

    assert result == created_document_id

    assert captured_request["title"] == "Database Backup"

    assert captured_request["content"] == (
        "Database backup verification procedure."
    )

    assert captured_request["source_type"] == "sop"

    assert captured_request["source_reference"] == (
        "knowledge/sop/database_backup.md"
    )

    assert captured_request["content_hash"] == (
        service.calculate_content_hash(
            "Database backup verification procedure."
        )
    )

    assert captured_request["metadata"] == {
        "category": "backup"
    }

    assert len(captured_request["chunks"]) == 1

    assert captured_request["chunks"][0]["chunk_index"] == 0

    assert captured_request["chunks"][0]["content"] == (
        "Database backup verification procedure."
    )

    assert len(
        captured_request["chunks"][0]["embedding"]
    ) == 1024


@pytest.mark.asyncio
async def test_ingest_file_loads_document_and_ingests_it(
    monkeypatch,
    tmp_path,
):
    service = KnowledgeService()

    file_path = tmp_path / "database_backup.md"

    file_path.write_text(
        "# Database Backup\n\nVerify the latest backup.",
        encoding="utf-8",
    )

    captured_request = {}
    created_document_id = 321

    async def mock_ingest_document(**kwargs):
        captured_request.update(kwargs)
        return created_document_id

    monkeypatch.setattr(
        service,
        "ingest_document",
        mock_ingest_document,
    )

    result = await service.ingest_file(
        str(file_path)
    )

    assert result == created_document_id

    assert captured_request["title"] == "database_backup"

    assert captured_request["content"] == (
        "# Database Backup\n\nVerify the latest backup."
    )

    assert captured_request["source_type"] == "internal"

    assert captured_request["source_reference"] == str(
        file_path
    )

    assert captured_request["metadata"] == {
        "file_name": "database_backup.md",
        "file_extension": ".md",
    }
