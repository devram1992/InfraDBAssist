from backend.app.auth.claims_mapper import ClaimsMapper
from backend.app.auth.jwt_authentication import JWTAuthenticationService
from backend.app.auth.jwt_validator import JWTValidator
from backend.app.auth.keycloak_config import KeycloakConfig
from backend.app.auth.keycloak_endpoints import KeycloakEndpoints
from backend.app.auth.keycloak_jwks_client import KeycloakJWKSClient


def create_keycloak_authentication_service(
    config: KeycloakConfig,
) -> JWTAuthenticationService:
    if not isinstance(config, KeycloakConfig):
        raise ValueError("config must be a KeycloakConfig.")

    endpoints = KeycloakEndpoints(config)

    jwks_client = KeycloakJWKSClient(
        jwks_url=endpoints.jwks_url,
    )

    validator = JWTValidator(
        issuer=endpoints.issuer,
        audience=config.client_id,
        algorithm="RS256",
        jwks_client=jwks_client,
    )

    claims_mapper = ClaimsMapper()

    return JWTAuthenticationService(
        token_validator=validator,
        claims_mapper=claims_mapper,
    )
