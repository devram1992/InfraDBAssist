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

    def __post_init__(self) -> None:
        if not self.server_url.strip():
            raise ValueError("server_url must not be empty.")

        if not self.realm.strip():
            raise ValueError("realm must not be empty.")

        if not self.client_id.strip():
            raise ValueError("client_id must not be empty.")