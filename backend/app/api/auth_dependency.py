from fastapi import HTTPException

from backend.app.auth.authentication import (
    AuthenticationService,
)
from backend.app.auth.user_context import UserContext


async def get_authenticated_user(
    authorization: str | None,
    authentication_service: AuthenticationService,
) -> UserContext:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required.",
        )

    if not authorization.startswith(
        "Bearer "
    ):
        raise HTTPException(
            status_code=401,
            detail="Bearer token is required.",
        )

    token = authorization[
        len("Bearer "):
    ].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Bearer token is required.",
        )

    try:
        return await authentication_service.authenticate(
            {
                "token": token,
            }
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc