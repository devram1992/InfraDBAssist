from pathlib import Path


class InternalDocumentClassifier:

    SOURCE_TYPES = {
        "runbooks": "runbook",
        "sop": "sop",
        "rca": "rca",
        "architecture": "architecture",
    }

    def classify(self, file_path: str) -> str:
        """
        Determine the knowledge source type from the
        document's parent directory.
        """

        path = Path(file_path)

        for directory_name, source_type in self.SOURCE_TYPES.items():
            if directory_name in path.parts:
                return source_type

        return "internal"
