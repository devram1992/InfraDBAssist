import httpx


class OllamaClient:

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:8b",
    ):
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str) -> str:
        """
        Send a prompt to the local Ollama model
        and return the generated response.
        """

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data.get("response", "")
