import pytest

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


def test_keycloak_config_rejects_empty_server_url():
    with pytest.raises(ValueError, match="server_url"):
        KeycloakConfig(
            server_url="",
            realm="infradb",
            client_id="infradb-assist",
        )


def test_keycloak_config_rejects_empty_realm():
    with pytest.raises(ValueError, match="realm"):
        KeycloakConfig(
            server_url="https://keycloak.example.com",
            realm="",
            client_id="infradb-assist",
        )


def test_keycloak_config_rejects_empty_client_id():
    with pytest.raises(ValueError, match="client_id"):
        KeycloakConfig(
            server_url="https://keycloak.example.com",
            realm="infradb",
            client_id="",
        )