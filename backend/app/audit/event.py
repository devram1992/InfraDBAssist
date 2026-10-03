from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuditEvent:
    """
    Immutable audit record for an InfraDB Assist operation.
    """

    user_id: str
    username: str
    roles: frozenset[str]
    tool_name: str
    permission: str
    request: dict
    status: str
    error: str | None = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
