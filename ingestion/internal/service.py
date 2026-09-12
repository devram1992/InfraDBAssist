from backend.app.knowledge.service import KnowledgeService

from ingestion.internal.classifier import InternalDocumentClassifier
from ingestion.internal.discovery import InternalDocumentDiscovery


class InternalIngestionService:

    def __init__(self):
        self.discovery = InternalDocumentDiscovery()
        self.classifier = InternalDocumentClassifier()
        self.knowledge_service = KnowledgeService()

    async def ingest_directory(self, directory: str) -> list[dict]:
        """
        Discover and ingest all supported internal knowledge
        documents under the supplied directory.
        """

        files = self.discovery.discover(directory)

        results = []

        for file_path in files:
            source_type = self.classifier.classify(file_path)

            document = self.knowledge_service.document_loader.load(
                file_path
            )

            document_id = await self.knowledge_service.ingest_document(
                title=document["title"],
                content=document["content"],
                source_type=source_type,
                source_reference=document["source_reference"],
                metadata=document["metadata"],
            )

            results.append(
                {
                    "document_id": document_id,
                    "file_path": file_path,
                    "source_type": source_type,
                    "status": "success",
                }
            )

        return results
