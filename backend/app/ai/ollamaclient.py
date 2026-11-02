import json

import httpx

from backend.app.config.settings import Settings


class OllamaClient:
    """Asynchronous client for the local Ollama HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ):
        configured_url = (
            base_url
            if base_url is not None
            else Settings.ollama_base_url
        )
        self.base_url = configured_url.rstrip("/")
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

    async def health_check(self) -> dict:
        """
        Check whether Ollama is reachable and whether the configured
        model is available locally.

        Connection and HTTP errors are returned as an unavailable status,
        making this method suitable for health APIs.
        """
        try:
            async with httpx.AsyncClient(
                timeout=min(self.timeout, 10.0)
            ) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags"
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return {
                "status": "unavailable",
                "available": False,
                "model": self.model,
                "model_available": False,
                "error": str(exc),
            }

        if not isinstance(data, dict) or not isinstance(
            data.get("models"), list
        ):
            return {
                "status": "unavailable",
                "available": False,
                "model": self.model,
                "model_available": False,
                "error": "Ollama returned an invalid model-list response.",
            }

        installed_models = {
            item.get("name")
            for item in data["models"]
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
        }
        model_available = self.model in installed_models

        return {
            "status": "healthy" if model_available else "model_missing",
            "available": True,
            "model": self.model,
            "model_available": model_available,
            "installed_models": sorted(installed_models),
        }

    async def generate(self, prompt: str) -> str:
        """
        Send a prompt to the configured local Ollama model and return
        its generated response.

        HTTP, connection, and timeout exceptions propagate to the caller
        so the application can handle operational failures explicitly.
        """
        if not isinstance(prompt, str):
            raise ValueError("Prompt must be a string.")

        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
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

        if not isinstance(data, dict):
            raise ValueError("Ollama returned an invalid response.")

        generated_text = data.get("response")

        if not isinstance(generated_text, str):
            raise ValueError(
                "Ollama response does not contain a valid text result."
            )

        return generated_text

    async def generate_json(self, prompt: str) -> dict:
        """
        Generate a response and parse it as a JSON object.

        Arrays and scalar JSON values are rejected because structured
        orchestration responses require a JSON object.
        """
        response = await self.generate(prompt)
        response = response.strip()

        try:
            result = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "LLM returned JSON that is not an object."
            )

        return result
