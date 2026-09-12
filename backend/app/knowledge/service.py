import hashlib

from ingestion.internal.loader import InternalDocumentLoader

from backend.app.ai.embedding import EmbeddingClient
from backend.app.database.repository import KnowledgeRepository
from backend.app.knowledge.chunker import DocumentChunker


class KnowledgeService:

    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.repository = KnowledgeRepository()
        self.chunker = DocumentChunker()
        self.document_loader = InternalDocumentLoader()

    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """
        Calculate a SHA-256 hash for document content.
        """

        if not content or not content.strip():
            raise ValueError(
                "Document content cannot be empty."
            )

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    async def ingest_document(
        self,
        title: str,
        content: str,
        source_type: str,
        source_reference: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """
        Store or update a knowledge document.

        Behavior:

        - New document:
          Create document, chunks, and embeddings.

        - Existing document with unchanged content:
          Skip ingestion and return existing document ID.

        - Existing document with changed content:
          Generate all new embeddings first, then replace the
          document and chunks atomically.
        """

        if not title or not title.strip():
            raise ValueError(
                "Document title cannot be empty."
            )

        if not content or not content.strip():
            raise ValueError(
                "Document content cannot be empty."
            )

        content_hash = self.calculate_content_hash(
            content
        )

        existing_document = None

        if source_reference:
            existing_document = (
                self.repository.get_document_by_source_reference(
                    source_reference
                )
            )

        # Existing document with unchanged content.
        if (
            existing_document
            and existing_document["content_hash"] == content_hash
        ):
            return existing_document["id"]

        # Split the document before making database changes.
        chunks = self.chunker.split(content)

        # Generate every embedding before changing the database.
        chunk_data = []

        for chunk_index, chunk_content in enumerate(chunks):

            embedding = await self.embedding_client.embed(
                chunk_content
            )

            chunk_data.append(
                {
                    "chunk_index": chunk_index,
                    "content": chunk_content,
                    "embedding": embedding,
                    "metadata": metadata,
                }
            )

        # New document.
        if existing_document is None:

            document_id = self.repository.create_document(
                title=title,
                content=content,
                source_type=source_type,
                source_reference=source_reference,
                metadata=metadata,
            )

            try:
                self.repository.update_content_hash(
                    document_id=document_id,
                    content_hash=content_hash,
                )

                self.repository.replace_document_chunks(
                    document_id=document_id,
                    chunks=chunk_data,
                )

            except Exception:
                try:
                    self.repository.delete_document(
                        document_id
                    )
                except Exception:
                    pass

                raise

            return document_id

        # Existing document with changed content.
        document_id = existing_document["id"]

        self.repository.replace_document(
            document_id=document_id,
            title=title,
            content=content,
            source_type=source_type,
            metadata=metadata,
            content_hash=content_hash,
            chunks=chunk_data,
        )

        return document_id

    async def ingest_file(
        self,
        file_path: str,
    ) -> int:
        """
        Load a local internal knowledge document and ingest it
        into the knowledge base.
        """

        document = self.document_loader.load(
            file_path
        )

        return await self.ingest_document(
            title=document["title"],
            content=document["content"],
            source_type=document["source_type"],
            source_reference=document["source_reference"],
            metadata=document["metadata"],
        )