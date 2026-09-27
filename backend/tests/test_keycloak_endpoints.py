from backend.app.auth.keycloak_config import KeycloakConfig
from backend.app.auth.keycloak_endpoints import KeycloakEndpoints


def test_keycloak_issuer_endpoint():
    config = KeycloakConfig(
        server_url="https://keycloak.example.com",
        realm="infradb",
        client_id="infradb-assist",
    )

    endpoints = KeycloakEndpoints(config)

    assert (
        endpoints.issuer
        == "https://keycloak.example.com/realms/infradb"
    )


def test_keycloak_jwks_endpoint():
    config = KeycloakConfig(
        server_url="https://keycloak.example.com",
        realm="infradb",
        client_id="infradb-assist",
    )

    endpoints = KeycloakEndpoints(config)

    assert (
        endpoints.jwks_url
        == (
            "https://keycloak.example.com/realms/"
            "infradb/protocol/openid-connect/certs"
        )
    )


def test_keycloak_server_url_trailing_slash_is_handled():
    config = KeycloakConfig(
        server_url="https://keycloak.example.com/",
        realm="infradb",
        client_id="infradb-assist",
    )

    endpoints = KeycloakEndpoints(config)

    assert (
        endpoints.issuer
        == "https://keycloak.example.com/realms/infradb"
    )


def test_invalid_config_is_rejected():
    try:
        KeycloakEndpoints("invalid")
        assert False
    except ValueError as exc:
        assert str(exc) == (
            "config must be a KeycloakConfig."
        )
