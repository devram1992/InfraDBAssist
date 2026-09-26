import pytest

from backend.app.auth.provider import (
    StaticAuthenticationProvider,
)


def test_static_provider_returns_user_context():
    provider = StaticAuthenticationProvider()

    context = provider.get_user_context(
        token="poc-token"
    )

    assert context.user_id == "poc-user"
    assert context.username == "engineer"
    assert context.roles == {
        "database_engineer"
    }
    assert context.permissions == {
        "database.read",
        "infrastructure.read",
        "kubernetes.read",
        "capacity.read",
    }


def test_static_provider_rejects_empty_token():
    provider = StaticAuthenticationProvider()

    with pytest.raises(
        ValueError,
        match="Authentication token is required",
    ):
        provider.get_user_context("")
