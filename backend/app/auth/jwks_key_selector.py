class JWKSKeySelector:
    """
    Selects an RSA signing key from a JWKS document
    using the JWT key ID (kid).
    """

    def select(
        self,
        jwks: dict,
        kid: str,
    ) -> dict:
        if not isinstance(jwks, dict):
            raise ValueError(
                "JWKS must be a dictionary."
            )

        if not kid:
            raise ValueError(
                "JWT 'kid' is required."
            )

        keys = jwks.get("keys")

        if not isinstance(keys, list):
            raise ValueError(
                "JWKS 'keys' must be a list."
            )

        for key in keys:
            if not isinstance(key, dict):
                continue

            if key.get("kid") != kid:
                continue

            if key.get("kty") != "RSA":
                raise ValueError(
                    "JWT signing key must be RSA."
                )

            return key

        raise ValueError(
            f"No RSA signing key found for kid '{kid}'."
        )
