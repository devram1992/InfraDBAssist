import pytest

from backend.app.auth.claims_mapper import ClaimsMapper
from backend.app.auth.jwt_authentication import (
    JWTAuthenticationService,
)
from backend.app.auth.token_validator import TokenValidator
from backend.app.auth.user_context import UserContext


class DummyTokenValidator(TokenValidator):

    async def validate(
        self,
        token: str,
    ) -> dict:
        return {
            "sub": "user-001",
            "preferred_username": "engineer",
            "realm_access": {
                "roles": [
                    "database_engineer",
                ],
            },
            "permissions": [
                "database.read",
            ],
        }


@pytest.mark.asyncio
async def test_jwt_authentication_returns_user_context():

    service = JWTAuthenticationService(
        token_validator=DummyTokenValidator(),
        claims_mapper=ClaimsMapper(),
    )

    context = await service.authenticate(
        {
            "token": "test-token",
        }
    )

    assert isinstance(
        context,
        UserContext,
    )

    assert context.user_id == "user-001"
    assert context.username == "engineer"

    assert context.roles == {
        "database_engineer",
    }

    assert context.permissions == {
        "database.read",
    }


@pytest.mark.asyncio
async def test_jwt_authentication_requires_token():

    service = JWTAuthenticationService(
        token_validator=DummyTokenValidator(),
        claims_mapper=ClaimsMapper(),
    )

    with pytest.raises(
        ValueError,
        match="token is required",
    ):
        await service.authenticate({})


@pytest.mark.asyncio
async def test_jwt_authentication_propagates_validation_error():

    class FailingTokenValidator(TokenValidator):

        async def validate(
            self,
            token: str,
        ) -> dict:
            raise ValueError(
                "Invalid JWT"
            )

    service = JWTAuthenticationService(
        token_validator=FailingTokenValidator(),
        claims_mapper=ClaimsMapper(),
    )

    with pytest.raises(
        ValueError,
        match="Invalid JWT",
    ):
        await service.authenticate(
            {
                "token": "bad-token",
            }
        )
