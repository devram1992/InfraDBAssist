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

    def clear(self) -> None:
        self._events.clear()
