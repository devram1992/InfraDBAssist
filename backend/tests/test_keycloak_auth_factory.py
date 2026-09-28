from backend.app.auth.jwt_authentication import JWTAuthenticationService
from backend.app.auth.keycloak_auth_factory import (
    create_keycloak_authentication_service,
)
from backend.app.auth.keycloak_config import KeycloakConfig


def test_create_keycloak_authentication_service():
    config = KeycloakConfig(
        server_url="https://keycloak.example.com",
        realm="infradb",
        client_id="infradb-assist",
    )

    service = create_keycloak_authentication_service(config)

    assert isinstance(service, JWTAuthenticationService)


def test_create_keycloak_authentication_service_rejects_invalid_config():
    try:
        create_keycloak_authentication_service("invalid")
        assert False
    except ValueError as exc:
        assert str(exc) == "config must be a KeycloakConfig."
