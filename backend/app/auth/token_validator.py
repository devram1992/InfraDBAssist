from abc import ABC, abstractmethod


class TokenValidator(ABC):
    """
    Boundary for validating authentication tokens.

    Implementations may validate JWT/OIDC tokens using
    Keycloak or another identity provider.
    """

    @abstractmethod
    async def validate(
        self,
        token: str,
    ) -> dict:
        """
        Validate the supplied token and return
        the validated token claims.
        """
        pass
