from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserContext:
    """
    Represents the authenticated user's authorization context.

    Permissions will later be populated from the authentication
    and RBAC layer, such as Keycloak.
    """

    user_id: str
    username: str
    roles: set[str] = field(default_factory=set)
    permissions: set[str] = field(default_factory=set)

    def has_permission(
        self,
        permission: str,
    ) -> bool:
        if not permission:
            return False

        return permission in self.permissions
