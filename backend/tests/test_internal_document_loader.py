import pytest

from ingestion.internal.loader import InternalDocumentLoader


def test_loader_loads_markdown_file(tmp_path):
    file_path = tmp_path / "database_backup.md"

    file_path.write_text(
        "# Database Backup\n\nVerify the latest backup.",
        encoding="utf-8",
    )

    loader = InternalDocumentLoader()

    result = loader.load(str(file_path))

    assert result["title"] == "database_backup"
    assert result["content"] == (
        "# Database Backup\n\nVerify the latest backup."
    )
    assert result["source_type"] == "internal"
    assert result["source_reference"] == str(file_path)
    assert result["metadata"]["file_name"] == "database_backup.md"
    assert result["metadata"]["file_extension"] == ".md"


def test_loader_loads_text_file(tmp_path):
    file_path = tmp_path / "runbook.txt"

    file_path.write_text(
        "Check database connectivity.",
        encoding="utf-8",
    )

    loader = InternalDocumentLoader()

    result = loader.load(str(file_path))

    assert result["title"] == "runbook"
    assert result["content"] == "Check database connectivity."
    assert result["metadata"]["file_extension"] == ".txt"


def test_loader_rejects_missing_file():
    loader = InternalDocumentLoader()

    with pytest.raises(
        FileNotFoundError,
        match="Knowledge document not found",
    ):
        loader.load(
            "knowledge/missing_document.md"
        )


def test_loader_rejects_directory(tmp_path):
    directory = tmp_path / "knowledge"
    directory.mkdir()

    loader = InternalDocumentLoader()

    with pytest.raises(
        ValueError,
        match="Knowledge document path is not a file",
    ):
        loader.load(str(directory))


def test_loader_rejects_unsupported_file_type(tmp_path):
    file_path = tmp_path / "document.pdf"

    file_path.write_text(
        "PDF placeholder",
        encoding="utf-8",
    )

    loader = InternalDocumentLoader()

    with pytest.raises(
        ValueError,
        match="Unsupported document type: .pdf",
    ):
        loader.load(str(file_path))


def test_loader_rejects_empty_file(tmp_path):
    file_path = tmp_path / "empty.md"

    file_path.write_text(
        "",
        encoding="utf-8",
    )

    loader = InternalDocumentLoader()

    with pytest.raises(
        ValueError,
        match="Knowledge document is empty",
    ):
        loader.load(str(file_path))


def test_loader_rejects_whitespace_only_file(tmp_path):
    file_path = tmp_path / "empty.md"

    file_path.write_text(
        "   \n\t  ",
        encoding="utf-8",
    )

    loader = InternalDocumentLoader()

    with pytest.raises(
        ValueError,
        match="Knowledge document is empty",
    ):
        loader.load(str(file_path))
