from backend.app.audit.event import AuditEvent
from backend.app.audit.service import AuditService
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
        -> audit
        -> request validation
        -> tool execution
    """

    def __init__(
        self,
        authorization: AuthorizationService,
        audit_service: AuditService,
    ):
        self.authorization = authorization
        self.audit_service = audit_service

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
            self.audit_service.record(
                AuditEvent(
                    user_id=user_context.user_id,
                    username=user_context.username,
                    roles=frozenset(user_context.roles),
                    tool_name=tool.name,
                    permission=tool.permission,
                    request=request,
                    status="denied",
                    error=(
                        f"Permission denied: "
                        f"{tool.permission}"
                    ),
                )
            )

            raise PermissionError(
                f"Permission denied: {tool.permission}"
            )

        try:
            tool.validate_request(request)
        except Exception as exc:
            self.audit_service.record(
                AuditEvent(
                    user_id=user_context.user_id,
                    username=user_context.username,
                    roles=frozenset(user_context.roles),
                    tool_name=tool.name,
                    permission=tool.permission,
                    request=request,
                    status="validation_failed",
                    error=str(exc),
                )
            )
            raise

        try:
            result = await tool.execute(request)
        except Exception as exc:
            self.audit_service.record(
                AuditEvent(
                    user_id=user_context.user_id,
                    username=user_context.username,
                    roles=frozenset(user_context.roles),
                    tool_name=tool.name,
                    permission=tool.permission,
                    request=request,
                    status="error",
                    error=str(exc),
                )
            )
            raise

        self.audit_service.record(
            AuditEvent(
                user_id=user_context.user_id,
                username=user_context.username,
                roles=frozenset(user_context.roles),
                tool_name=tool.name,
                permission=tool.permission,
                request=request,
                status="success",
            )
        )

        return result