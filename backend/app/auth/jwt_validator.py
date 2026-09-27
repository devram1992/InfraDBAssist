import jwt

from backend.app.auth.jwks_key_selector import (
    JWKSKeySelector,
)
from backend.app.auth.token_validator import TokenValidator


class JWTValidator(TokenValidator):
    """
    JWT token validator.

    Supports validation using either:
    - a directly supplied signing key, or
    - a JWKS provider with kid-based key selection.
    """

    def __init__(
        self,
        signing_key=None,
        issuer: str = "",
        audience: str = "",
        algorithm: str = "RS256",
        jwks_client=None,
        key_selector: JWKSKeySelector | None = None,
    ):
        if not signing_key and jwks_client is None:
            raise ValueError(
                "Either signing_key or jwks_client is required."
            )

        if not issuer:
            raise ValueError(
                "issuer is required."
            )

        if not audience:
            raise ValueError(
                "audience is required."
            )

        if not algorithm:
            raise ValueError(
                "algorithm is required."
            )

        self.signing_key = signing_key
        self.issuer = issuer
        self.audience = audience
        self.algorithm = algorithm
        self.jwks_client = jwks_client
        self.key_selector = (
            key_selector or JWKSKeySelector()
        )

    async def validate(
        self,
        token: str,
    ) -> dict:
        if not token:
            raise ValueError(
                "token is required."
            )

        signing_key = self.signing_key

        if self.jwks_client is not None:
            try:
                header = jwt.get_unverified_header(
                    token
                )
            except jwt.PyJWTError as exc:
                raise ValueError(
                    f"Invalid JWT header: {exc}"
                ) from exc

            kid = header.get("kid")

            if not kid:
                raise ValueError(
                    "JWT header missing required 'kid'."
                )

            jwks = await self.jwks_client.get_keys()

            selected_key = (
                self.key_selector.select(
                    jwks,
                    kid,
                )
            )

            try:
                signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(
                    selected_key
                )
            except Exception as exc:
                raise ValueError(
                    f"Invalid RSA signing key: {exc}"
                ) from exc

        try:
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
            )
        except jwt.PyJWTError as exc:
            raise ValueError(
                f"Invalid JWT: {exc}"
            ) from exc

        if not claims.get("sub"):
            raise ValueError(
                "JWT claims missing required 'sub'."
            )

        return claims