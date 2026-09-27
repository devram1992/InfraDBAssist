import pytest
from fastapi import HTTPException

from backend.app.auth.user_context import UserContext
from backend.app.api.auth_dependency import (
    get_authenticated_user,
)


class DummyAuthenticationService:

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
async def test_authenticated_user_is_returned():

    user = await get_authenticated_user(
        authorization="Bearer test-token",
        authentication_service=DummyAuthenticationService(),
    )

    assert isinstance(
        user,
        UserContext,
    )

    assert user.user_id == "user-001"
    assert user.username == "engineer"


@pytest.mark.asyncio
async def test_missing_authorization_header_is_rejected():

    with pytest.raises(
        HTTPException,
    ) as exc:

        await get_authenticated_user(
            authorization=None,
            authentication_service=DummyAuthenticationService(),
        )

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_invalid_authorization_scheme_is_rejected():

    with pytest.raises(
        HTTPException,
    ) as exc:

        await get_authenticated_user(
            authorization="Basic abc123",
            authentication_service=DummyAuthenticationService(),
        )

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_empty_bearer_token_is_rejected():

    with pytest.raises(
        HTTPException,
    ) as exc:

        await get_authenticated_user(
            authorization="Bearer ",
            authentication_service=DummyAuthenticationService(),
        )

    assert exc.value.status_code == 401