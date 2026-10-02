from backend.app.auth.authorization import AuthorizationService
from backend.app.auth.user_context import UserContext
from backend.app.tools.base import Tool


class ToolExecutor:
    """
    Controlled execution boundary for InfraDB Assist tools.

    Execution flow:
        type validation
        -> user context validation
        -> authorization
        -> request validation
        -> tool execution
    """

    def __init__(
        self,
        authorization: AuthorizationService,
    ):
        self.authorization = authorization

    async def execute(
        self,
        tool: Tool,
        request: dict,
        user_context: UserContext | None = None,
    ) -> dict:
        if not isinstance(
            tool,
            Tool,
        ):
            raise TypeError(
                "tool must be an instance of Tool."
            )

        if user_context is None:
            raise ValueError(
                "User context is required."
            )

        allowed = (
            self.authorization.is_user_allowed(
                user_context=user_context,
                required_permission=tool.permission,
            )
        )

        if not allowed:
            raise PermissionError(
                f"Permission denied: {tool.permission}"
            )

        tool.validate_request(request)

        return await tool.execute(request)