import httpx


class EmbeddingClient:

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "bge-m3",
    ):
        self.base_url = base_url
        self.model = model

    async def embed(self, text: str) -> list[float]:
        """
        Generate an embedding using the local Ollama embedding model.
        """

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        payload = {
            "model": self.model,
            "input": text,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

        embeddings = data.get("embeddings")

        if not embeddings:
            raise ValueError(
                "Ollama returned no embeddings."
            )

        embedding = embeddings[0]

        if len(embedding) != 1024:
            raise ValueError(
                f"Expected 1024 dimensions, "
                f"received {len(embedding)}."
            )

        return embedding