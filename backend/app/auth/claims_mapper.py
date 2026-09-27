from backend.app.auth.role_permissions import (
    RolePermissionMapper,
)
from backend.app.auth.user_context import UserContext


class ClaimsMapper:
    """
    Maps validated identity-provider claims into
    the application's UserContext.
    """

    def __init__(
        self,
        role_permission_mapper: RolePermissionMapper | None = None,
    ):
        self.role_permission_mapper = (
            role_permission_mapper
            or RolePermissionMapper()
        )

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

        realm_access = claims.get(
            "realm_access",
            {}
        )

        if isinstance(realm_access, dict):
            realm_roles = realm_access.get(
                "roles",
                []
            )

            if isinstance(realm_roles, list):
                roles.update(realm_roles)

        resource_access = claims.get(
            "resource_access",
            {}
        )

        if isinstance(resource_access, dict):
            client_access = resource_access.get(
                "infradb-assist",
                {}
            )

            if isinstance(client_access, dict):
                client_roles = client_access.get(
                    "roles",
                    []
                )

                if isinstance(client_roles, list):
                    roles.update(client_roles)

        role_permissions = (
            self.role_permission_mapper.get_permissions(
                roles
            )
        )

        claim_permissions = set(
            claims.get("permissions", [])
        )

        permissions = (
            role_permissions | claim_permissions
        )

        return UserContext(
            user_id=user_id,
            username=username,
            roles=roles,
            permissions=permissions,
        )