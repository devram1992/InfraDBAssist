from backend.app.auth.provider import AuthenticationProvider
from backend.app.auth.user_context import UserContext


class AuthenticationService:
    """
    Service responsible for resolving the authenticated user.

    The service delegates authentication to the configured
    AuthenticationProvider and returns a UserContext.
    """

    def __init__(
        self,
        provider: AuthenticationProvider,
    ):
        if not isinstance(
            provider,
            AuthenticationProvider,
        ):
            raise TypeError(
                "provider must be an AuthenticationProvider."
            )

        self.provider = provider

    def authenticate(
        self,
        token: str,
    ) -> UserContext:
        if not token:
            raise ValueError(
                "Authentication token is required."
            )

        return self.provider.get_user_context(
            token
        )
