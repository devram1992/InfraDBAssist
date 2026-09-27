from abc import ABC, abstractmethod


class JWKSClient(ABC):
    """
    Boundary for retrieving JSON Web Key Sets (JWKS).

    Implementations are responsible for retrieving public
    signing keys from an identity provider such as Keycloak.
    """

    @abstractmethod
    async def get_keys(self) -> dict:
        """
        Retrieve and return the JWKS document.
        """
        pass
