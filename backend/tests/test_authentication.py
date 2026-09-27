import pytest

from backend.app.auth.authentication import AuthenticationService
from backend.app.auth.user_context import UserContext


class DummyAuthenticationService(
    AuthenticationService
):
    async def authenticate(
        self,
        credentials: dict,
    ) -> UserContext:
        return UserContext(
            user_id="user-001",
            username="engineer",
            roles={"database_engineer"},
            permissions={"database.read"},
        )


@pytest.mark.asyncio
async def test_authentication_returns_user_context():
    service = DummyAuthenticationService()

    context = await service.authenticate(
        credentials={
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
        "database_engineer"
    }
    assert context.permissions == {
        "database.read"
    }


@pytest.mark.asyncio
async def test_authentication_is_defined_as_async_boundary():
    service = DummyAuthenticationService()

    result = await service.authenticate({})

    assert isinstance(
        result,
        UserContext,
    )
