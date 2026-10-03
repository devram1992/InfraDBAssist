from dataclasses import dataclass, field
from datetime import datetime, timezone


class AuditEvent:
    """
    Immutable audit record for an InfraDB Assist operation.

    The event validates its core fields when created so malformed
    audit records cannot enter the audit service.
    """

    VALID_STATUSES = frozenset(
        {
            "success",
            "denied",
            "validation_failed",
            "error",
        }
    )

    def __init__(
        self,
        user_id: str,
        username: str,
        roles: frozenset[str],
        tool_name: str,
        permission: str,
        request: dict,
        status: str,
        error: str | None = None,
        timestamp: datetime | None = None,
    ):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string.")

        if not isinstance(username, str) or not username.strip():
            raise ValueError("username must be a non-empty string.")

        if not isinstance(roles, frozenset):
            raise TypeError("roles must be a frozenset.")

        if not all(isinstance(role, str) and role.strip() for role in roles):
            raise ValueError("roles must contain only non-empty strings.")

        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("tool_name must be a non-empty string.")

        if not isinstance(permission, str) or not permission.strip():
            raise ValueError("permission must be a non-empty string.")

        if not isinstance(request, dict):
            raise TypeError("request must be a dictionary.")

        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid audit status: {status!r}."
            )

        if error is not None and not isinstance(error, str):
            raise TypeError("error must be a string or None.")

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        if not isinstance(timestamp, datetime):
            raise TypeError("timestamp must be a datetime.")

        if timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware.")

        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "username", username)
        object.__setattr__(self, "roles", roles)
        object.__setattr__(self, "tool_name", tool_name)
        object.__setattr__(self, "permission", permission)
        object.__setattr__(self, "request", request)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "error", error)
        object.__setattr__(self, "timestamp", timestamp)

    def __setattr__(self, name, value):
        raise AttributeError("AuditEvent is immutable.")