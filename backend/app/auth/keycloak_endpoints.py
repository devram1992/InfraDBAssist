
from backend.app.auth.keycloak_config import KeycloakConfig


class KeycloakEndpoints:
    """
    Builds standard Keycloak OpenID Connect endpoints.
    """

    def __init__(
        self,
        config: KeycloakConfig,
    ):
        if not isinstance(config, KeycloakConfig):
            raise ValueError(
                "config must be a KeycloakConfig."
            )

        self.config = config

    @property
    def issuer(self) -> str:
        return (
            f"{self.config.server_url.rstrip('/')}"
            f"/realms/{self.config.realm}"
        )

    @property
    def jwks_url(self) -> str:
        if self.config.jwks_url:
            return self.config.jwks_url.rstrip("/")

        return (
            f"{self.issuer}"
            f"/protocol/openid-connect/certs"
        )
