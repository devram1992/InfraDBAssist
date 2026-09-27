from abc import ABC, abstractmethod

from backend.app.auth.user_context import UserContext


class AuthenticationService(ABC):
    """
    Authentication boundary for InfraDB Assist.

    Implementations are responsible for validating an identity
    and returning an authenticated UserContext.
    """

    @abstractmethod
    async def authenticate(
        self,
        credentials: dict,
    ) -> UserContext:
        """
        Authenticate the supplied credentials and return
        the authenticated user's context.
        """
        pass
