from backend.app.ai.embedding import EmbeddingClient
from backend.app.config.settings import Settings
from backend.app.database.repository import KnowledgeRepository


class RAGService:

    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.repository = KnowledgeRepository()

    async def search(
        self,
        question: str,
        limit: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[dict]:
        """
        Search the knowledge base using chunk-level
        semantic similarity.
        """

        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        if limit is None:
            limit = Settings.rag_default_limit

        if limit < 1:
            raise ValueError(
                "Limit must be greater than zero."
            )

        if similarity_threshold is None:
            similarity_threshold = (
                Settings.rag_similarity_threshold
            )

        if not 0 <= similarity_threshold <= 1:
            raise ValueError(
                "Similarity threshold must be between 0 and 1."
            )

        embedding = await self.embedding_client.embed(
            question
        )

        return self.repository.search_similar_chunks(
            embedding=embedding,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )