import httpx

from backend.app.auth.jwks_client import JWKSClient


class KeycloakJWKSClient(JWKSClient):
    """
    Retrieves public signing keys from a Keycloak JWKS endpoint.
    """

    def __init__(
        self,
        jwks_url: str,
        timeout: float = 5.0,
    ):
        if not jwks_url:
            raise ValueError(
                "jwks_url is required."
            )

        if timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

        self.jwks_url = jwks_url
        self.timeout = timeout

    async def get_keys(self) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.get(
                    self.jwks_url
                )

                response.raise_for_status()

                data = response.json()

        except httpx.HTTPError as exc:
            raise ValueError(
                f"Unable to retrieve JWKS: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "JWKS response must be a dictionary."
            )

        if "keys" not in data:
            raise ValueError(
                "JWKS response missing 'keys'."
            )

        if not isinstance(data["keys"], list):
            raise ValueError(
                "JWKS 'keys' must be a list."
            )

        return data
