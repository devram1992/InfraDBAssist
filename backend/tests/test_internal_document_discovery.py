import pytest

from ingestion.internal.discovery import InternalDocumentDiscovery


def test_discovery_finds_supported_files_recursively(tmp_path):
    runbooks = tmp_path / "runbooks"
    nested = runbooks / "database"

    nested.mkdir(parents=True)

    markdown_file = runbooks / "oracle.md"
    text_file = nested / "backup.txt"

    markdown_file.write_text(
        "Oracle runbook",
        encoding="utf-8",
    )

    text_file.write_text(
        "Backup procedure",
        encoding="utf-8",
    )

    discovery = InternalDocumentDiscovery()

    results = discovery.discover(str(tmp_path))

    assert results == sorted(
        [
            str(markdown_file),
            str(text_file),
        ]
    )


def test_discovery_ignores_unsupported_files(tmp_path):
    markdown_file = tmp_path / "runbook.md"
    pdf_file = tmp_path / "document.pdf"
    docx_file = tmp_path / "document.docx"

    markdown_file.write_text(
        "Runbook",
        encoding="utf-8",
    )

    pdf_file.write_text(
        "PDF placeholder",
        encoding="utf-8",
    )

    docx_file.write_text(
        "DOCX placeholder",
        encoding="utf-8",
    )

    discovery = InternalDocumentDiscovery()

    results = discovery.discover(str(tmp_path))

    assert results == [
        str(markdown_file),
    ]


def test_discovery_returns_empty_list_for_empty_directory(
    tmp_path,
):
    discovery = InternalDocumentDiscovery()

    results = discovery.discover(str(tmp_path))

    assert results == []


def test_discovery_rejects_missing_directory():
    discovery = InternalDocumentDiscovery()

    with pytest.raises(
        FileNotFoundError,
        match="Knowledge directory not found",
    ):
        discovery.discover(
            "knowledge/missing_directory"
        )


def test_discovery_rejects_file_path(tmp_path):
    file_path = tmp_path / "document.md"

    file_path.write_text(
        "Knowledge document",
        encoding="utf-8",
    )

    discovery = InternalDocumentDiscovery()

    with pytest.raises(
        ValueError,
        match="Knowledge path is not a directory",
    ):
        discovery.discover(str(file_path))
