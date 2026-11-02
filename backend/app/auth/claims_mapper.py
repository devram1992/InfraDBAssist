
from backend.app.auth.role_permissions import (
    RolePermissionMapper,
)
from backend.app.auth.user_context import UserContext


class ClaimsMapper:
    """
    Maps validated identity-provider claims into
    the application's UserContext.

    Application permissions are derived exclusively
    from trusted application role mappings.
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

        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError(
                "Token claims missing required 'sub'."
            )

        if not isinstance(username, str) or not username.strip():
            raise ValueError(
                "Token claims missing required "
                "'preferred_username'."
            )

        roles: set[str] = set()

        # Extract direct application roles.
        direct_roles = claims.get("roles", [])

        if isinstance(direct_roles, list):
            roles.update(
                role
                for role in direct_roles
                if isinstance(role, str) and role.strip()
            )

        # Extract Keycloak realm roles.
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
                roles.update(
                    role
                    for role in realm_roles
                    if isinstance(role, str) and role.strip()
                )

        # Extract InfraDBAssist client roles.
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
                    roles.update(
                        role
                        for role in client_roles
                        if isinstance(role, str) and role.strip()
                    )

        # Derive permissions exclusively from application roles.
        # Never trust arbitrary permissions supplied in JWT claims.
        permissions = (
            self.role_permission_mapper.get_permissions(
                roles
            )
        )

        return UserContext(
            user_id=user_id,
            username=username,
            roles=roles,
            permissions=permissions,
        )
