from backend.app.ai.embedding import EmbeddingClient
from backend.app.database.repository import KnowledgeRepository


class RAGService:

    def __init__(self):
        self.embedding_client = EmbeddingClient()
        self.repository = KnowledgeRepository()

    async def search(
        self,
        question: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search the knowledge base using semantic similarity.
        """

        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        embedding = await self.embedding_client.embed(
            question
        )

        return self.repository.search_similar(
            embedding=embedding,
            limit=limit,
        )
