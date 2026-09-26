class AuthorizationService:
    """
    Lightweight permission checker for InfraDB Assist.

    Authorization is based on explicit permission strings.
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
