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

def test_audit_event_rejects_empty_user_id():
    with pytest.raises(
        ValueError,
        match="user_id must be a non-empty string",
    ):
        AuditEvent(
            user_id="",
            username="database-engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            request={},
            status="success",
        )


def test_audit_event_rejects_empty_username():
    with pytest.raises(
        ValueError,
        match="username must be a non-empty string",
    ):
        AuditEvent(
            user_id="user-001",
            username="   ",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            request={},
            status="success",
        )


def test_audit_event_rejects_invalid_roles_type():
    with pytest.raises(
        TypeError,
        match="roles must be a frozenset",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles={"database_engineer"},
            tool_name="postgresql",
            permission="database.read",
            request={},
            status="success",
        )


def test_audit_event_rejects_invalid_role_value():
    with pytest.raises(
        ValueError,
        match="roles must contain only non-empty strings",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles=frozenset({"database_engineer", ""}),
            tool_name="postgresql",
            permission="database.read",
            request={},
            status="success",
        )


def test_audit_event_rejects_empty_tool_name():
    with pytest.raises(
        ValueError,
        match="tool_name must be a non-empty string",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="",
            permission="database.read",
            request={},
            status="success",
        )


def test_audit_event_rejects_empty_permission():
    with pytest.raises(
        ValueError,
        match="permission must be a non-empty string",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="",
            request={},
            status="success",
        )


def test_audit_event_rejects_invalid_request_type():
    with pytest.raises(
        TypeError,
        match="request must be a dictionary",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            request=[],
            status="success",
        )


def test_audit_event_rejects_invalid_status():
    with pytest.raises(
        ValueError,
        match="Invalid audit status",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            request={},
            status="unknown",
        )


def test_audit_event_rejects_invalid_error_type():
    with pytest.raises(
        TypeError,
        match="error must be a string or None",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            request={},
            status="error",
            error=123,
        )


def test_audit_event_rejects_naive_timestamp():
    with pytest.raises(
        ValueError,
        match="timestamp must be timezone-aware",
    ):
        AuditEvent(
            user_id="user-001",
            username="database-engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            request={},
            status="success",
            timestamp=datetime.now(),
        )


@pytest.mark.parametrize(
    "status",
    [
        "success",
        "denied",
        "validation_failed",
        "error",
    ],
)
def test_audit_event_accepts_valid_statuses(status):
    event = build_event(status=status)

    assert event.status == status


def test_audit_event_accepts_explicit_utc_timestamp():
    timestamp = datetime(
        2026,
        10,
        3,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    event = AuditEvent(
        user_id="user-001",
        username="database-engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        request={"action": "health"},
        status="success",
        timestamp=timestamp,
    )

    assert event.timestamp == timestamp
