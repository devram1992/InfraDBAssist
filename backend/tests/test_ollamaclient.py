import pytest
import httpx

from backend.app.ai.ollamaclient import OllamaClient


def test_ollama_client_loads_settings():
    client = OllamaClient()

    assert client.base_url == "http://localhost:11434"
    assert client.model == "qwen3:8b"
    assert client.timeout == 300.0


def test_ollama_client_allows_overrides():
    client = OllamaClient(
        base_url="http://test-host:11434",
        model="test-model",
        timeout=60.0,
    )

    assert client.base_url == "http://test-host:11434"
    assert client.model == "test-model"
    assert client.timeout == 60.0


@pytest.mark.asyncio
async def test_generate_success(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "response": "InfraDB Assist OK",
            }

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, json):
            assert url == "http://localhost:11434/api/generate"
            assert json["model"] == "qwen3:8b"
            assert json["prompt"] == "Test prompt"
            assert json["stream"] is False
            assert json["think"] is False
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.ai.ollamaclient.httpx.AsyncClient",
        MockAsyncClient,
    )

    client = OllamaClient()

    result = await client.generate("Test prompt")

    assert result == "InfraDB Assist OK"


@pytest.mark.asyncio
async def test_generate_json_success(monkeypatch):
    client = OllamaClient()

    async def mock_generate(prompt):
        return '{"tool": "oracle_database", "parameters": {"database": "PRODDB"}}'

    monkeypatch.setattr(
        client,
        "generate",
        mock_generate,
    )

    result = await client.generate_json("Select Oracle tool")

    assert result == {
        "tool": "oracle_database",
        "parameters": {
            "database": "PRODDB",
        },
    }


@pytest.mark.asyncio
async def test_generate_json_invalid_json(monkeypatch):
    client = OllamaClient()

    async def mock_generate(prompt):
        return "not valid json"

    monkeypatch.setattr(
        client,
        "generate",
        mock_generate,
    )

    with pytest.raises(ValueError, match="LLM returned invalid JSON"):
        await client.generate_json("Select tool")


@pytest.mark.asyncio
async def test_generate_http_error(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "Server error",
                request=httpx.Request(
                    "POST",
                    "http://localhost:11434/api/generate",
                ),
                response=httpx.Response(500),
            )

        def json(self):
            return {}

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, json):
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.ai.ollamaclient.httpx.AsyncClient",
        MockAsyncClient,
    )

    client = OllamaClient()

    with pytest.raises(httpx.HTTPStatusError):
        await client.generate("Test prompt")
