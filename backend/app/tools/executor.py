from backend.app.auth.authorization import AuthorizationService
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
        user_permissions: set[str],
    ) -> dict:
        if not isinstance(tool, Tool):
            raise TypeError("tool must be an instance of Tool.")

        if not self.authorization.is_allowed(
            user_permissions=user_permissions,
            required_permission=tool.permission,
        ):
            raise PermissionError(
                f"Permission denied: {tool.permission}"
            )

        tool.validate_request(request)

        return await tool.execute(request)
