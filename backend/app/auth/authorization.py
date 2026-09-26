from backend.app.auth.user_context import UserContext


class AuthorizationService:
    """
    Permission checker for InfraDB Assist.

    Authorization can be evaluated using either an explicit
    permission set or an authenticated UserContext.
    """

    def is_allowed(
        self,
        user_permissions: set[str],
        required_permission: str,
    ) -> bool:
        if not isinstance(user_permissions, set):
            raise ValueError(
                "user_permissions must be a set."
            )

        if not required_permission:
            return False

        return required_permission in user_permissions

    def is_user_allowed(
        self,
        user_context: UserContext,
        required_permission: str,
    ) -> bool:
        if not isinstance(
            user_context,
            UserContext,
        ):
            raise ValueError(
                "user_context must be a UserContext."
            )

        if not required_permission:
            return False

        return user_context.has_permission(
            required_permission
        )
