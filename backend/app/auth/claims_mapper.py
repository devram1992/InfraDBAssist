from backend.app.auth.user_context import UserContext


class ClaimsMapper:
    """
    Maps validated identity-provider claims into
    the application's UserContext.
    """

    def to_user_context(
        self,
        claims: dict,
    ) -> UserContext:
        if not isinstance(claims, dict):
            raise ValueError(
                "Claims must be a dictionary."
            )

        user_id = claims.get("sub")
        username = claims.get(
            "preferred_username"
        )

        if not user_id:
            raise ValueError(
                "Token claims missing required 'sub'."
            )

        if not username:
            raise ValueError(
                "Token claims missing required "
                "'preferred_username'."
            )

        roles = set(
            claims.get("roles", [])
        )

        permissions = set(
            claims.get("permissions", [])
        )

        return UserContext(
            user_id=user_id,
            username=username,
            roles=roles,
            permissions=permissions,
        )
