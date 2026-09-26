from abc import ABC, abstractmethod

from backend.app.auth.user_context import UserContext


class AuthenticationProvider(ABC):
    """
    Contract for authentication providers.

    Implementations are responsible for resolving the authenticated
    user into a UserContext.
    """

    @abstractmethod
    def get_user_context(
        self,
        token: str,
    ) -> UserContext:
        pass


class StaticAuthenticationProvider(
    AuthenticationProvider
):
    """
    Temporary POC authentication provider.

    This implementation does not validate a real token.
    It returns a fixed UserContext for local development.
    """

    def get_user_context(
        self,
        token: str,
    ) -> UserContext:
        if not token:
            raise ValueError(
                "Authentication token is required."
            )

        return UserContext(
            user_id="poc-user",
            username="engineer",
            roles={"database_engineer"},
            permissions={
                "database.read",
                "infrastructure.read",
                "kubernetes.read",
                "capacity.read",
            },
        )
