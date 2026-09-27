from typing import Final


class RolePermissionMapper:
    """
    Maps application roles to InfraDB Assist permissions.
    """

    ROLE_PERMISSIONS: Final[dict[str, set[str]]] = {
        "database_engineer": {
            "database.read",
        },
        "infrastructure_engineer": {
            "infrastructure.read",
        },
        "kubernetes_engineer": {
            "kubernetes.read",
        },
        "capacity_engineer": {
            "capacity.read",
        },
        "platform_engineer": {
            "database.read",
            "infrastructure.read",
            "kubernetes.read",
            "capacity.read",
        },
        "admin": {
            "database.read",
            "infrastructure.read",
            "kubernetes.read",
            "capacity.read",
        },
    }

    def get_permissions(
        self,
        roles: set[str],
    ) -> set[str]:
        if not isinstance(roles, set):
            raise ValueError(
                "roles must be a set."
            )

        permissions: set[str] = set()

        for role in roles:
            permissions.update(
                self.ROLE_PERMISSIONS.get(
                    role,
                    set(),
                )
            )

        return permissions
