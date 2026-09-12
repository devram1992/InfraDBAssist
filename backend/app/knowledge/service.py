from backend.app.ai.embedding import EmbeddingClient
from backend.app.database.repository import KnowledgeRepository
from backend.app.knowledge.chunker import DocumentChunker


class KnowledgeService:

    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.repository = KnowledgeRepository()
        self.chunker = DocumentChunker()

    async def ingest_document(
        self,
        title: str,
        content: str,
        source_type: str,
        source_reference: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """
        Store a knowledge document, split it into chunks,
        generate embeddings, and store the chunks.
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

        try:
            chunks = self.chunker.split(content)

            for chunk_index, chunk_content in enumerate(chunks):
                chunk_id = self.repository.create_chunk(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    content=chunk_content,
                    metadata=metadata,
                )

                embedding = await self.embedding_client.embed(
                    chunk_content
                )

                self.repository.update_chunk_embedding(
                    chunk_id=chunk_id,
                    embedding=embedding,
                )

        except Exception:
            try:
                self.repository.delete_document(
                    document_id=document_id
                )
            except Exception:
                pass

            raise

        return document_id
