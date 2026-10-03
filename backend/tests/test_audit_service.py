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


def build_event_with(
    *,
    user_id: str = "user-001",
    tool_name: str = "postgresql",
    status: str = "success",
    timestamp: datetime | None = None,
) -> AuditEvent:
    return AuditEvent(
        user_id=user_id,
        username="database-engineer",
        roles=frozenset({"database_engineer"}),
        tool_name=tool_name,
        permission="database.read",
        request={"action": "health"},
        status=status,
        timestamp=timestamp,
    )


def test_audit_service_find_by_user():
    service = AuditService()

    user_event = build_event_with(user_id="user-001")
    other_event = build_event_with(user_id="user-002")

    service.record(user_event)
    service.record(other_event)

    events = service.find_by_user("user-001")

    assert events == [user_event]


def test_audit_service_find_by_user_returns_empty_for_unknown_user():
    service = AuditService()

    service.record(build_event_with(user_id="user-001"))

    assert service.find_by_user("unknown-user") == []


def test_audit_service_find_by_tool():
    service = AuditService()

    postgres_event = build_event_with(tool_name="postgresql")
    oracle_event = build_event_with(tool_name="oracle")

    service.record(postgres_event)
    service.record(oracle_event)

    events = service.find_by_tool("postgresql")

    assert events == [postgres_event]


def test_audit_service_find_by_tool_returns_empty_for_unknown_tool():
    service = AuditService()

    service.record(build_event_with(tool_name="postgresql"))

    assert service.find_by_tool("unknown-tool") == []


def test_audit_service_find_by_status():
    service = AuditService()

    success_event = build_event_with(status="success")
    denied_event = build_event_with(status="denied")
    error_event = build_event_with(status="error")

    service.record(success_event)
    service.record(denied_event)
    service.record(error_event)

    events = service.find_by_status("denied")

    assert events == [denied_event]


def test_audit_service_find_by_status_returns_empty_when_no_match():
    service = AuditService()

    service.record(build_event_with(status="success"))

    assert service.find_by_status("error") == []


def test_audit_service_find_by_time_range():
    service = AuditService()

    first = datetime(
        2026,
        10,
        3,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )
    second = datetime(
        2026,
        10,
        3,
        11,
        0,
        0,
        tzinfo=timezone.utc,
    )
    third = datetime(
        2026,
        10,
        3,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    first_event = build_event_with(timestamp=first)
    second_event = build_event_with(timestamp=second)
    third_event = build_event_with(timestamp=third)

    service.record(first_event)
    service.record(second_event)
    service.record(third_event)

    events = service.find_by_time_range(
        start_time=second,
        end_time=third,
    )

    assert events == [
        second_event,
        third_event,
    ]


def test_audit_service_find_by_time_range_includes_boundaries():
    service = AuditService()

    timestamp = datetime(
        2026,
        10,
        3,
        11,
        0,
        0,
        tzinfo=timezone.utc,
    )

    event = build_event_with(timestamp=timestamp)
    service.record(event)

    events = service.find_by_time_range(
        start_time=timestamp,
        end_time=timestamp,
    )

    assert events == [event]


def test_audit_service_rejects_empty_user_filter():
    service = AuditService()

    with pytest.raises(
        ValueError,
        match="user_id must be a non-empty string",
    ):
        service.find_by_user("")


def test_audit_service_rejects_empty_tool_filter():
    service = AuditService()

    with pytest.raises(
        ValueError,
        match="tool_name must be a non-empty string",
    ):
        service.find_by_tool("")


def test_audit_service_rejects_invalid_status_filter():
    service = AuditService()

    with pytest.raises(
        ValueError,
        match="Invalid audit status",
    ):
        service.find_by_status("unknown")


def test_audit_service_rejects_naive_time_range():
    service = AuditService()

    start_time = datetime(2026, 10, 3, 10, 0, 0)
    end_time = datetime(
        2026,
        10,
        3,
        11,
        0,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="start_time must be timezone-aware",
    ):
        service.find_by_time_range(
            start_time=start_time,
            end_time=end_time,
        )


def test_audit_service_rejects_invalid_time_range_order():
    service = AuditService()

    start_time = datetime(
        2026,
        10,
        3,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )
    end_time = datetime(
        2026,
        10,
        3,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="start_time must be before or equal to end_time",
    ):
        service.find_by_time_range(
            start_time=start_time,
            end_time=end_time,
        )
