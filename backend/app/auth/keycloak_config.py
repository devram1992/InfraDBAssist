from dataclasses import dataclass


@dataclass(frozen=True)
class KeycloakConfig:
    """
    Configuration required to communicate with Keycloak.
    """

    server_url: str
    realm: str
    client_id: str
    client_secret: str | None = None
