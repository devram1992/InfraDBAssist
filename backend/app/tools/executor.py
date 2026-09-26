from backend.app.auth.authorization import AuthorizationService
from backend.app.auth.user_context import UserContext
from backend.app.tools.base import Tool


class ToolExecutor:
    """
    Controlled execution boundary for InfraDB Assist tools.

    Execution flow:
        type validation
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
        user_permissions: set[str] | None = None,
        user_context: UserContext | None = None,
    ) -> dict:
        if not isinstance(
            tool,
            Tool,
        ):
            raise TypeError(
                "tool must be an instance of Tool."
            )

        if user_context is not None:
            allowed = (
                self.authorization.is_user_allowed(
                    user_context=user_context,
                    required_permission=tool.permission,
                )
            )

        elif user_permissions is not None:
            allowed = (
                self.authorization.is_allowed(
                    user_permissions=user_permissions,
                    required_permission=tool.permission,
                )
            )

        else:
            raise ValueError(
                "Either user_context or "
                "user_permissions must be provided."
            )

        if not allowed:
            raise PermissionError(
                f"Permission denied: {tool.permission}"
            )

        tool.validate_request(request)

        return await tool.execute(request)