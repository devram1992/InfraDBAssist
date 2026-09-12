from backend.app.ai.embedding import EmbeddingClient
from backend.app.database.repository import KnowledgeRepository


class KnowledgeService:

    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.repository = KnowledgeRepository()

    async def ingest_document(
        self,
        title: str,
        content: str,
        source_type: str,
        source_reference: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """
        Store a knowledge document and generate its embedding.
        """

        if not title or not title.strip():
            raise ValueError(
                "Document title cannot be empty."
            )

        if not content or not content.strip():
            raise ValueError(
                "Document content cannot be empty."
            )

        document_id = self.repository.create_document(
            title=title,
            content=content,
            source_type=source_type,
            source_reference=source_reference,
            metadata=metadata,
        )

        embedding = await self.embedding_client.embed(
            content
        )

        self.repository.update_embedding(
            document_id=document_id,
            embedding=embedding,
        )

        return document_id
