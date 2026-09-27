from backend.app.auth.keycloak_config import KeycloakConfig


def test_keycloak_config():
    config = KeycloakConfig(
        server_url="https://keycloak.example.com",
        realm="infradb",
        client_id="infradb-assist",
        client_secret="test-secret",
    )

    assert config.server_url == "https://keycloak.example.com"
    assert config.realm == "infradb"
    assert config.client_id == "infradb-assist"
    assert config.client_secret == "test-secret"


def test_keycloak_config_without_secret():
    config = KeycloakConfig(
        server_url="https://keycloak.example.com",
        realm="infradb",
        client_id="infradb-assist",
    )

    assert config.client_secret is None
