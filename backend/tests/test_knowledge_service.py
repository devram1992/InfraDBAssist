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