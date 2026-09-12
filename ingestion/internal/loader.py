from pathlib import Path


class InternalDocumentLoader:

    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".md",
    }

    def load(self, file_path: str) -> dict:
        """
        Load a local internal knowledge document.

        Returns the document content and basic source metadata.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Knowledge document not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Knowledge document path is not a file: {file_path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document type: {path.suffix}"
            )

        content = path.read_text(encoding="utf-8")

        if not content.strip():
            raise ValueError(
                f"Knowledge document is empty: {file_path}"
            )

        return {
            "title": path.stem,
            "content": content,
            "source_type": "internal",
            "source_reference": str(path),
            "metadata": {
                "file_name": path.name,
                "file_extension": path.suffix.lower(),
            },
        }

