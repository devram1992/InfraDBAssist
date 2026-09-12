import pytest

from ingestion.internal.service import InternalIngestionService


@pytest.mark.asyncio
async def test_ingest_directory_processes_discovered_files(
    monkeypatch,
):
    service = InternalIngestionService()

    discovered_files = [
        "knowledge/runbooks/oracle_performance.md",
        "knowledge/sop/database_backup.md",
    ]

    documents = {
        discovered_files[0]: {
            "title": "oracle_performance",
            "content": "Oracle performance troubleshooting",
            "source_reference": discovered_files[0],
            "metadata": {
                "file_name": "oracle_performance.md",
            },
        },
        discovered_files[1]: {
            "title": "database_backup",
            "content": "Database backup verification",
            "source_reference": discovered_files[1],
            "metadata": {
                "file_name": "database_backup.md",
            },
        },
    }

    async def mock_ingest_document(**kwargs):
        if kwargs["title"] == "oracle_performance":
            return 101

        if kwargs["title"] == "database_backup":
            return 102

        raise AssertionError(
            f"Unexpected document: {kwargs['title']}"
        )

    monkeypatch.setattr(
        service.discovery,
        "discover",
        lambda directory: discovered_files,
    )

    monkeypatch.setattr(
        service.classifier,
        "classify",
        lambda file_path: (
            "runbook"
            if "runbooks" in file_path
            else "sop"
        ),
    )

    monkeypatch.setattr(
        service.knowledge_service.document_loader,
        "load",
        lambda file_path: documents[file_path],
    )

    monkeypatch.setattr(
        service.knowledge_service,
        "ingest_document",
        mock_ingest_document,
    )

    results = await service.ingest_directory(
        "knowledge"
    )

    assert results == [
        {
            "document_id": 101,
            "file_path": discovered_files[0],
            "source_type": "runbook",
            "status": "success",
        },
        {
            "document_id": 102,
            "file_path": discovered_files[1],
            "source_type": "sop",
            "status": "success",
        },
    ]


@pytest.mark.asyncio
async def test_ingest_directory_returns_empty_list_when_no_files_found(
    monkeypatch,
):
    service = InternalIngestionService()

    monkeypatch.setattr(
        service.discovery,
        "discover",
        lambda directory: [],
    )

    results = await service.ingest_directory(
        "knowledge"
    )

    assert results == []
