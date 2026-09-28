import os

from backend.app.auth.keycloak_config import KeycloakConfig


def load_keycloak_config() -> KeycloakConfig:
    server_url = os.getenv("KEYCLOAK_SERVER_URL", "")
    realm = os.getenv("KEYCLOAK_REALM", "")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID", "")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")

    return KeycloakConfig(
        server_url=server_url,
        realm=realm,
        client_id=client_id,
        client_secret=client_secret,
    )
