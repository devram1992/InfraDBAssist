import httpx
import pytest

from backend.app.ai.ollamaclient import OllamaClient


def test_ollama_client_loads_settings():
    client = OllamaClient()

    assert client.base_url == "http://localhost:11434"
    assert client.model == "qwen3:8b"
    assert client.timeout == 300.0


def test_ollama_client_allows_overrides():
    client = OllamaClient(
        base_url="http://test-host:11434/",
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
            return {"response": "InfraDB Assist OK"}

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

    result = await OllamaClient().generate("Test prompt")
    assert result == "InfraDB Assist OK"


@pytest.mark.asyncio
async def test_generate_rejects_empty_prompt():
    with pytest.raises(ValueError, match="Prompt must not be empty"):
        await OllamaClient().generate("   ")


@pytest.mark.asyncio
async def test_generate_rejects_non_string_prompt():
    with pytest.raises(ValueError, match="Prompt must be a string"):
        await OllamaClient().generate(None)


@pytest.mark.asyncio
async def test_generate_rejects_invalid_response_shape(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected": "value"}

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

    with pytest.raises(
        ValueError,
        match="does not contain a valid text result",
    ):
        await OllamaClient().generate("Test prompt")


@pytest.mark.asyncio
async def test_generate_json_success(monkeypatch):
    client = OllamaClient()

    async def mock_generate(prompt):
        return (
            '{"tool": "oracle_database", '
            '"parameters": {"database": "DEVDB"}}'
        )

    monkeypatch.setattr(client, "generate", mock_generate)

    result = await client.generate_json("Select Oracle tool")

    assert result == {
        "tool": "oracle_database",
        "parameters": {"database": "DEVDB"},
    }


@pytest.mark.asyncio
async def test_generate_json_invalid_json(monkeypatch):
    client = OllamaClient()

    async def mock_generate(prompt):
        return "not valid json"

    monkeypatch.setattr(client, "generate", mock_generate)

    with pytest.raises(ValueError, match="LLM returned invalid JSON"):
        await client.generate_json("Select tool")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response_text",
    ['["one", "two"]', '"text"', "123", "null"],
)
async def test_generate_json_requires_object(monkeypatch, response_text):
    client = OllamaClient()

    async def mock_generate(prompt):
        return response_text

    monkeypatch.setattr(client, "generate", mock_generate)

    with pytest.raises(
        ValueError,
        match="LLM returned JSON that is not an object",
    ):
        await client.generate_json("Return an object")


@pytest.mark.asyncio
async def test_generate_http_error_propagates(monkeypatch):
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

    with pytest.raises(httpx.HTTPStatusError):
        await OllamaClient().generate("Test prompt")


@pytest.mark.asyncio
async def test_health_check_success_and_model_available(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "models": [
                    {"name": "qwen3:8b"},
                    {"name": "bge-m3:latest"},
                ]
            }

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            assert kwargs["timeout"] == 10.0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            assert url == "http://localhost:11434/api/tags"
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.ai.ollamaclient.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = await OllamaClient().health_check()

    assert result["status"] == "healthy"
    assert result["available"] is True
    assert result["model"] == "qwen3:8b"
    assert result["model_available"] is True
    assert result["installed_models"] == [
        "bge-m3:latest",
        "qwen3:8b",
    ]


@pytest.mark.asyncio
async def test_health_check_reports_missing_model(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"models": [{"name": "bge-m3:latest"}]}

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.ai.ollamaclient.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = await OllamaClient().health_check()

    assert result["status"] == "model_missing"
    assert result["available"] is True
    assert result["model_available"] is False


@pytest.mark.asyncio
async def test_health_check_reports_connection_failure(monkeypatch):
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            raise httpx.ConnectError(
                "Connection refused",
                request=httpx.Request(
                    "GET",
                    "http://localhost:11434/api/tags",
                ),
            )

    monkeypatch.setattr(
        "backend.app.ai.ollamaclient.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = await OllamaClient().health_check()

    assert result["status"] == "unavailable"
    assert result["available"] is False
    assert result["model_available"] is False
    assert "Connection refused" in result["error"]


@pytest.mark.asyncio
async def test_health_check_rejects_invalid_tags_response(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected": []}

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            return MockResponse()

    monkeypatch.setattr(
        "backend.app.ai.ollamaclient.httpx.AsyncClient",
        MockAsyncClient,
    )

    result = await OllamaClient().health_check()

    assert result["status"] == "unavailable"
    assert result["available"] is False
    assert "invalid model-list response" in result["error"]
