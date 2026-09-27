import pytest

from backend.app.auth.provider import (
    StaticAuthenticationProvider,
)
from backend.app.auth.service import (
    AuthenticationService,
)


def test_authentication_service_returns_user_context():
    provider = StaticAuthenticationProvider()
    service = AuthenticationService(provider)

    context = service.authenticate(
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


def test_authentication_service_rejects_empty_token():
    provider = StaticAuthenticationProvider()
    service = AuthenticationService(provider)

    with pytest.raises(
        ValueError,
        match="Authentication token is required",
    ):
        service.authenticate("")


def test_authentication_service_rejects_invalid_provider():
    with pytest.raises(
        TypeError,
        match="provider must be an AuthenticationProvider",
    ):
        AuthenticationService(object())
