import json

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

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data.get("response", "")

    async def generate_json(self, prompt: str) -> dict:
        """
        Send a prompt to the local Ollama model and
        parse the response as JSON.
        """

        response = await self.generate(prompt)

        response = response.strip()

        try:
            return json.loads(response)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM returned invalid JSON: {response}"
            ) from exc