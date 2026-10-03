from datetime import datetime, timezone

import pytest

from backend.app.audit.event import AuditEvent
from backend.app.audit.service import AuditService


def build_event(
    status: str = "success",
    error: str | None = None,
) -> AuditEvent:
    return AuditEvent(
        user_id="user-001",
        username="database-engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        request={"action": "health"},
        status=status,
        error=error,
    )


def test_audit_event_creates_utc_timestamp():
    event = build_event()

    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo == timezone.utc


def test_audit_event_is_immutable():
    event = build_event()

    with pytest.raises(AttributeError):
        event.status = "denied"


def test_audit_service_records_event():
    service = AuditService()
    event = build_event()

    service.record(event)

    events = service.list_events()

    assert len(events) == 1
    assert events[0] == event


def test_audit_service_records_failed_event():
    service = AuditService()

    event = build_event(
        status="denied",
        error="Permission denied: database.read",
    )

    service.record(event)

    recorded = service.list_events()[0]

    assert recorded.status == "denied"
    assert recorded.error == (
        "Permission denied: database.read"
    )


def test_audit_service_returns_copy_of_events():
    service = AuditService()
    event = build_event()

    service.record(event)

    events = service.list_events()
    events.clear()

    assert len(service.list_events()) == 1


def test_audit_service_rejects_invalid_event():
    service = AuditService()

    with pytest.raises(
        TypeError,
        match="event must be an AuditEvent",
    ):
        service.record(None)


def test_audit_service_clear():
    service = AuditService()

    service.record(build_event())
    service.record(build_event())

    assert len(service.list_events()) == 2

    service.clear()

    assert service.list_events() == []
