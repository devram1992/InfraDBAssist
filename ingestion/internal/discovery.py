from pathlib import Path


class InternalDocumentDiscovery:

    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".md",
    }

    def discover(self, directory: str) -> list[str]:
        """
        Discover supported internal knowledge documents
        recursively under the supplied directory.
        """

        path = Path(directory)

        if not path.exists():
            raise FileNotFoundError(
                f"Knowledge directory not found: {directory}"
            )

        if not path.is_dir():
            raise ValueError(
                f"Knowledge path is not a directory: {directory}"
            )

        files = [
            str(file_path)
            for file_path in path.rglob("*")
            if file_path.is_file()
            and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]

        return sorted(files)
