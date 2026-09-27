import jwt

from backend.app.auth.token_validator import TokenValidator


class JWTValidator(TokenValidator):
    """
    JWT token validator.

    Validates a JWT using the supplied signing key and
    expected issuer/audience values.
    """

    def __init__(
        self,
        signing_key: str,
        issuer: str,
        audience: str,
        algorithm: str = "RS256",
    ):
        if not signing_key:
            raise ValueError(
                "signing_key is required."
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

    async def validate(
        self,
        token: str,
    ) -> dict:
        if not token:
            raise ValueError(
                "token is required."
            )

        try:
            claims = jwt.decode(
                token,
                self.signing_key,
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
