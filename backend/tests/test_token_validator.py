import pytest

from backend.app.auth.token_validator import TokenValidator


class DummyTokenValidator(TokenValidator):
    async def validate(
        self,
        token: str,
    ) -> dict:
        return {
            "sub": "user-001",
            "preferred_username": "engineer",
            "roles": [
                "database_engineer",
            ],
        }


@pytest.mark.asyncio
async def test_token_validator_returns_claims():
    validator = DummyTokenValidator()

    claims = await validator.validate(
        "test-token"
    )

    assert claims["sub"] == "user-001"
    assert claims["preferred_username"] == "engineer"
    assert claims["roles"] == [
        "database_engineer",
    ]


@pytest.mark.asyncio
async def test_token_validator_is_async_boundary():
    validator = DummyTokenValidator()

    result = await validator.validate(
        "test-token"
    )

    assert isinstance(result, dict)
