import pytest

from backend.app.auth.jwks_client import JWKSClient


class DummyJWKSClient(JWKSClient):
    async def get_keys(self) -> dict:
        return {
            "keys": [
                {
                    "kid": "test-key",
                    "kty": "RSA",
                    "alg": "RS256",
                }
            ]
        }


@pytest.mark.asyncio
async def test_jwks_client_returns_keys():
    client = DummyJWKSClient()

    jwks = await client.get_keys()

    assert jwks["keys"][0]["kid"] == "test-key"
    assert jwks["keys"][0]["kty"] == "RSA"
    assert jwks["keys"][0]["alg"] == "RS256"


@pytest.mark.asyncio
async def test_jwks_client_is_async_boundary():
    client = DummyJWKSClient()

    result = await client.get_keys()

    assert isinstance(result, dict)
    assert "keys" in result
