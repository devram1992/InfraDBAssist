from datetime import datetime

from backend.app.audit.event import AuditEvent


class AuditService:
    """
    In-memory audit event service.

    This is intentionally storage-agnostic. Persistent storage
    can be introduced later without changing callers.
    """

    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        if not isinstance(event, AuditEvent):
            raise TypeError(
                "event must be an AuditEvent."
            )

        self._events.append(event)

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)

    def find_by_user(
        self,
        user_id: str,
    ) -> list[AuditEvent]:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError(
                "user_id must be a non-empty string."
            )

        return [
            event
            for event in self._events
            if event.user_id == user_id
        ]

    def find_by_tool(
        self,
        tool_name: str,
    ) -> list[AuditEvent]:
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError(
                "tool_name must be a non-empty string."
            )

        return [
            event
            for event in self._events
            if event.tool_name == tool_name
        ]

    def find_by_status(
        self,
        status: str,
    ) -> list[AuditEvent]:
        if status not in AuditEvent.VALID_STATUSES:
            raise ValueError(
                f"Invalid audit status: {status!r}."
            )

        return [
            event
            for event in self._events
            if event.status == status
        ]

    def find_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[AuditEvent]:
        if not isinstance(start_time, datetime):
            raise TypeError(
                "start_time must be a datetime."
            )

        if not isinstance(end_time, datetime):
            raise TypeError(
                "end_time must be a datetime."
            )

        if start_time.tzinfo is None:
            raise ValueError(
                "start_time must be timezone-aware."
            )

        if end_time.tzinfo is None:
            raise ValueError(
                "end_time must be timezone-aware."
            )

        if start_time > end_time:
            raise ValueError(
                "start_time must be before or equal to end_time."
            )

        return [
            event
            for event in self._events
            if start_time <= event.timestamp <= end_time
        ]

    def clear(self) -> None:
        self._events.clear()