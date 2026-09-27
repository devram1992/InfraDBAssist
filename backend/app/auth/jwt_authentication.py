from backend.app.auth.authentication import AuthenticationService
from backend.app.auth.claims_mapper import ClaimsMapper
from backend.app.auth.token_validator import TokenValidator
from backend.app.auth.user_context import UserContext


class JWTAuthenticationService(
    AuthenticationService
):
    """
    Authenticates a JWT and converts its validated
    claims into an application UserContext.
    """

    def __init__(
        self,
        token_validator: TokenValidator,
        claims_mapper: ClaimsMapper,
    ):
        if not isinstance(
            token_validator,
            TokenValidator,
        ):
            raise ValueError(
                "token_validator must be a TokenValidator."
            )

        if not isinstance(
            claims_mapper,
            ClaimsMapper,
        ):
            raise ValueError(
                "claims_mapper must be a ClaimsMapper."
            )

        self.token_validator = token_validator
        self.claims_mapper = claims_mapper

    async def authenticate(
        self,
        credentials: dict,
    ) -> UserContext:

        if not isinstance(
            credentials,
            dict,
        ):
            raise ValueError(
                "credentials must be a dictionary."
            )

        token = credentials.get("token")

        if not token:
            raise ValueError(
                "token is required."
            )

        claims = await self.token_validator.validate(
            token
        )

        return self.claims_mapper.to_user_context(
            claims
        )
