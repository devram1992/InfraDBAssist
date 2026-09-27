import pytest

from backend.app.auth.jwks_key_selector import JWKSKeySelector


def test_matching_rsa_key_is_selected():
    selector = JWKSKeySelector()

    jwks = {
        "keys": [
            {
                "kid": "key-001",
                "kty": "RSA",
                "alg": "RS256",
            },
            {
                "kid": "key-002",
                "kty": "RSA",
                "alg": "RS256",
            },
        ]
    }

    result = selector.select(
        jwks,
        "key-002",
    )

    assert result["kid"] == "key-002"
    assert result["kty"] == "RSA"


def test_unknown_kid_is_rejected():
    selector = JWKSKeySelector()

    jwks = {
        "keys": [
            {
                "kid": "key-001",
                "kty": "RSA",
            }
        ]
    }

    with pytest.raises(
        ValueError,
        match="No RSA signing key found",
    ):
        selector.select(
            jwks,
            "unknown-key",
        )


def test_missing_kid_is_rejected():
    selector = JWKSKeySelector()

    with pytest.raises(
        ValueError,
        match="JWT 'kid' is required",
    ):
        selector.select(
            {"keys": []},
            "",
        )


def test_non_rsa_key_is_rejected():
    selector = JWKSKeySelector()

    jwks = {
        "keys": [
            {
                "kid": "key-001",
                "kty": "EC",
                "alg": "ES256",
            }
        ]
    }

    with pytest.raises(
        ValueError,
        match="signing key must be RSA",
    ):
        selector.select(
            jwks,
            "key-001",
        )


def test_invalid_jwks_is_rejected():
    selector = JWKSKeySelector()

    with pytest.raises(
        ValueError,
        match="JWKS must be a dictionary",
    ):
        selector.select(
            "invalid",
            "key-001",
        )


def test_invalid_keys_collection_is_rejected():
    selector = JWKSKeySelector()

    with pytest.raises(
        ValueError,
        match="JWKS 'keys' must be a list",
    ):
        selector.select(
            {"keys": "invalid"},
            "key-001",
        )
