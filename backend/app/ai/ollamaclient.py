import json

import httpx

from backend.app.config.settings import Settings


class OllamaClient:

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (
            base_url
            if base_url is not None
            else Settings.ollama_base_url
        )

        self.model = (
            model
            if model is not None
            else Settings.ollama_model
        )

        self.timeout = (
            timeout
            if timeout is not None
            else Settings.ollama_timeout
        )

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

        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:

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