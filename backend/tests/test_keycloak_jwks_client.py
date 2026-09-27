import httpx
import pytest

from backend.app.auth.keycloak_jwks_client import (
    KeycloakJWKSClient,
)


JWKS_URL = (
    "https://keycloak.example.com/"
    "realms/infradb/protocol/openid-connect/certs"
)


@pytest.mark.asyncio
async def test_jwks_client_retrieves_keys(monkeypatch):
    async def mock_get_keys(
        self,
        url,
    ):
        return httpx.Response(
            status_code=200,
            json={
                "keys": [
                    {
                        "kid": "key-001",
                        "kty": "RSA",
                        "alg": "RS256",
                    }
                ]
            },
            request=httpx.Request(
                "GET",
                url,
            ),
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get_keys,
    )

    client = KeycloakJWKSClient(
        jwks_url=JWKS_URL,
    )

    result = await client.get_keys()

    assert result["keys"][0]["kid"] == "key-001"


@pytest.mark.asyncio
async def test_http_error_is_converted_to_value_error(
    monkeypatch,
):
    async def mock_get_keys(
        self,
        url,
    ):
        request = httpx.Request(
            "GET",
            url,
        )

        raise httpx.ConnectError(
            "connection failed",
            request=request,
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get_keys,
    )

    client = KeycloakJWKSClient(
        jwks_url=JWKS_URL,
    )

    with pytest.raises(
        ValueError,
        match="Unable to retrieve JWKS",
    ):
        await client.get_keys()


@pytest.mark.asyncio
async def test_missing_keys_is_rejected(monkeypatch):
    async def mock_get_keys(
        self,
        url,
    ):
        return httpx.Response(
            status_code=200,
            json={},
            request=httpx.Request(
                "GET",
                url,
            ),
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get_keys,
    )

    client = KeycloakJWKSClient(
        jwks_url=JWKS_URL,
    )

    with pytest.raises(
        ValueError,
        match="missing 'keys'",
    ):
        await client.get_keys()


@pytest.mark.asyncio
async def test_keys_must_be_a_list(monkeypatch):
    async def mock_get_keys(
        self,
        url,
    ):
        return httpx.Response(
            status_code=200,
            json={
                "keys": "invalid",
            },
            request=httpx.Request(
                "GET",
                url,
            ),
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        mock_get_keys,
    )

    client = KeycloakJWKSClient(
        jwks_url=JWKS_URL,
    )

    with pytest.raises(
        ValueError,
        match="must be a list",
    ):
        await client.get_keys()


def test_jwks_url_is_required():
    with pytest.raises(
        ValueError,
        match="jwks_url is required",
    ):
        KeycloakJWKSClient("")


def test_timeout_must_be_positive():
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        KeycloakJWKSClient(
            JWKS_URL,
            timeout=0,
        )
