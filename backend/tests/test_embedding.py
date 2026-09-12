import httpx
import pytest

from backend.app.ai.embedding import EmbeddingClient


class MockResponse:

    def __init__(
        self,
        data,
        status_code=200,
    ):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "HTTP error",
                request=httpx.Request(
                    "POST",
                    "http://localhost:11434/api/embed",
                ),
                response=httpx.Response(
                    self.status_code,
                ),
            )

    def json(self):
        return self._data


class MockAsyncClient:

    def __init__(
        self,
        response,
    ):
        self.response = response
        self.posted_payload = None

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False

    async def post(
        self,
        url,
        json,
    ):
        self.posted_payload = {
            "url": url,
            "json": json,
        }

        return self.response


@pytest.mark.asyncio
async def test_embedding_client_generates_embedding(
    monkeypatch,
):
    embedding = [0.1] * 1024

    response = MockResponse(
        {
            "embeddings": [
                embedding,
            ]
        }
    )

    client_instance = MockAsyncClient(
        response
    )

    def mock_async_client(*args, **kwargs):
        return client_instance

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        mock_async_client,
    )

    client = EmbeddingClient()

    result = await client.embed(
        "Database backup verification"
    )

    assert result == embedding

    assert client_instance.posted_payload[
        "url"
    ] == "http://localhost:11434/api/embed"

    assert client_instance.posted_payload[
        "json"
    ] == {
        "model": "bge-m3",
        "input": "Database backup verification",
    }


@pytest.mark.asyncio
async def test_embedding_client_rejects_empty_text():
    client = EmbeddingClient()

    with pytest.raises(
        ValueError,
        match="Text cannot be empty.",
    ):
        await client.embed("")


@pytest.mark.asyncio
async def test_embedding_client_rejects_whitespace_text():
    client = EmbeddingClient()

    with pytest.raises(
        ValueError,
        match="Text cannot be empty.",
    ):
        await client.embed("   ")


@pytest.mark.asyncio
async def test_embedding_client_rejects_missing_embeddings(
    monkeypatch,
):
    response = MockResponse(
        {}
    )

    client_instance = MockAsyncClient(
        response
    )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: client_instance,
    )

    client = EmbeddingClient()

    with pytest.raises(
        ValueError,
        match="Ollama returned no embeddings.",
    ):
        await client.embed(
            "Database backup verification"
        )


@pytest.mark.asyncio
async def test_embedding_client_rejects_invalid_dimension(
    monkeypatch,
):
    embedding = [0.1] * 3

    response = MockResponse(
        {
            "embeddings": [
                embedding,
            ]
        }
    )

    client_instance = MockAsyncClient(
        response
    )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: client_instance,
    )

    client = EmbeddingClient()

    with pytest.raises(
        ValueError,
        match="Expected 1024 dimensions, received 3.",
    ):
        await client.embed(
            "Database backup verification"
        )


@pytest.mark.asyncio
async def test_embedding_client_raises_http_error(
    monkeypatch,
):
    response = MockResponse(
        {},
        status_code=500,
    )

    client_instance = MockAsyncClient(
        response
    )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: client_instance,
    )

    client = EmbeddingClient()

    with pytest.raises(
        httpx.HTTPStatusError
    ):
        await client.embed(
            "Database backup verification"
        )
