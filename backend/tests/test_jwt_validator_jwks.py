from datetime import datetime, timedelta, timezone
import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.app.auth.jwt_validator import JWTValidator


ISSUER = "https://keycloak.example.com/realms/infradb"
AUDIENCE = "infradb-assist"
KEY_ID = "key-001"


class DummyJWKSClient:
    def __init__(self, jwks):
        self.jwks = jwks

    async def get_keys(self):
        return self.jwks


def create_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    return (
        private_key,
        private_key.public_key(),
    )


def create_token(
    private_key,
    *,
    kid=KEY_ID,
):
    now = datetime.now(timezone.utc)

    claims = {
        "sub": "user-001",
        "preferred_username": "engineer",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }

    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={
            "kid": kid,
        },
    )


def create_jwks(public_key):
    public_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(
        public_key
    )

    jwk = json.loads(public_jwk)

    jwk["kid"] = KEY_ID
    jwk["alg"] = "RS256"
    jwk["use"] = "sig"

    return {
        "keys": [
            jwk,
        ]
    }


@pytest.mark.asyncio
async def test_jwks_signed_token_is_accepted():
    private_key, public_key = create_rsa_keys()

    jwks = create_jwks(public_key)

    validator = JWTValidator(
        issuer=ISSUER,
        audience=AUDIENCE,
        algorithm="RS256",
        jwks_client=DummyJWKSClient(jwks),
    )

    token = create_token(private_key)

    claims = await validator.validate(token)

    assert claims["sub"] == "user-001"
    assert claims["preferred_username"] == "engineer"


@pytest.mark.asyncio
async def test_unknown_kid_is_rejected():
    private_key, public_key = create_rsa_keys()

    jwks = create_jwks(public_key)

    validator = JWTValidator(
        issuer=ISSUER,
        audience=AUDIENCE,
        algorithm="RS256",
        jwks_client=DummyJWKSClient(jwks),
    )

    token = create_token(
        private_key,
        kid="unknown-key",
    )

    with pytest.raises(
        ValueError,
        match="No RSA signing key found",
    ):
        await validator.validate(token)


@pytest.mark.asyncio
async def test_missing_kid_is_rejected():
    private_key, public_key = create_rsa_keys()

    jwks = create_jwks(public_key)

    validator = JWTValidator(
        issuer=ISSUER,
        audience=AUDIENCE,
        algorithm="RS256",
        jwks_client=DummyJWKSClient(jwks),
    )

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "user-001",
            "preferred_username": "engineer",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
    )

    with pytest.raises(
        ValueError,
        match="missing required 'kid'",
    ):
        await validator.validate(token)


@pytest.mark.asyncio
async def test_jwks_client_is_called_for_validation():
    private_key, public_key = create_rsa_keys()

    jwks = create_jwks(public_key)

    client = DummyJWKSClient(jwks)

    validator = JWTValidator(
        issuer=ISSUER,
        audience=AUDIENCE,
        algorithm="RS256",
        jwks_client=client,
    )

    token = create_token(private_key)

    claims = await validator.validate(token)

    assert claims["sub"] == "user-001"