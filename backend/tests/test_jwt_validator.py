from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.app.auth.jwt_validator import JWTValidator


ISSUER = "https://keycloak.example.com/realms/infradb"
AUDIENCE = "infradb-assist"


@pytest.fixture
def rsa_keys():
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
    subject="user-001",
    issuer=ISSUER,
    audience=AUDIENCE,
    expires_delta=timedelta(minutes=5),
):
    now = datetime.now(timezone.utc)

    claims = {
        "sub": subject,
        "preferred_username": "engineer",
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
    )


def create_validator(public_key):
    return JWTValidator(
        signing_key=public_key,
        issuer=ISSUER,
        audience=AUDIENCE,
        algorithm="RS256",
    )


@pytest.mark.asyncio
async def test_valid_rs256_jwt_is_accepted(rsa_keys):
    private_key, public_key = rsa_keys

    validator = create_validator(public_key)

    token = create_token(private_key)

    claims = await validator.validate(token)

    assert claims["sub"] == "user-001"
    assert claims["preferred_username"] == "engineer"


@pytest.mark.asyncio
async def test_invalid_signature_is_rejected(rsa_keys):
    private_key, _ = rsa_keys

    wrong_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    wrong_public_key = wrong_private_key.public_key()

    validator = create_validator(wrong_public_key)

    token = create_token(private_key)

    with pytest.raises(
        ValueError,
        match="Invalid JWT",
    ):
        await validator.validate(token)


@pytest.mark.asyncio
async def test_invalid_issuer_is_rejected(rsa_keys):
    private_key, public_key = rsa_keys

    validator = create_validator(public_key)

    token = create_token(
        private_key,
        issuer="https://wrong-issuer",
    )

    with pytest.raises(
        ValueError,
        match="Invalid JWT",
    ):
        await validator.validate(token)


@pytest.mark.asyncio
async def test_invalid_audience_is_rejected(rsa_keys):
    private_key, public_key = rsa_keys

    validator = create_validator(public_key)

    token = create_token(
        private_key,
        audience="wrong-audience",
    )

    with pytest.raises(
        ValueError,
        match="Invalid JWT",
    ):
        await validator.validate(token)


@pytest.mark.asyncio
async def test_expired_token_is_rejected(rsa_keys):
    private_key, public_key = rsa_keys

    validator = create_validator(public_key)

    token = create_token(
        private_key,
        expires_delta=timedelta(minutes=-5),
    )

    with pytest.raises(
        ValueError,
        match="Invalid JWT",
    ):
        await validator.validate(token)


@pytest.mark.asyncio
async def test_missing_subject_is_rejected(rsa_keys):
    private_key, public_key = rsa_keys

    validator = create_validator(public_key)

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
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
        match="missing required 'sub'",
    ):
        await validator.validate(token)


@pytest.mark.asyncio
async def test_empty_token_is_rejected(rsa_keys):
    _, public_key = rsa_keys

    validator = create_validator(public_key)

    with pytest.raises(
        ValueError,
        match="token is required",
    ):
        await validator.validate("")


def test_validator_requires_signing_key():
    with pytest.raises(
        ValueError,
        match="signing_key is required",
    ):
        JWTValidator(
            signing_key="",
            issuer=ISSUER,
            audience=AUDIENCE,
        )


def test_validator_requires_issuer(rsa_keys):
    _, public_key = rsa_keys

    with pytest.raises(
        ValueError,
        match="issuer is required",
    ):
        JWTValidator(
            signing_key=public_key,
            issuer="",
            audience=AUDIENCE,
        )


def test_validator_requires_audience(rsa_keys):
    _, public_key = rsa_keys

    with pytest.raises(
        ValueError,
        match="audience is required",
    ):
        JWTValidator(
            signing_key=public_key,
            issuer=ISSUER,
            audience="",
        )