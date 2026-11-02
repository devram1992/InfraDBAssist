
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.app.audit.event import AuditEvent
from backend.app.auth.authentication import AuthenticationService
from backend.app.auth.jwt_authentication import JWTAuthenticationService
from backend.app.auth.user_context import UserContext
from backend.app.main import app


class DummyAuthenticationService(AuthenticationService):
    async def authenticate(
        self,
        credentials: dict,
    ) -> UserContext:
        token = credentials.get("token")

        if token == "invalid-token":
            raise ValueError("Invalid JWT")

        if token == "platform-token":
            return UserContext(
                user_id="platform-001",
                username="platform-engineer",
                roles={"platform_engineer"},
                permissions={
                    "database.read",
                    "infrastructure.read",
                    "kubernetes.read",
                    "capacity.read",
                    "audit.read",
                },
            )

        if token == "admin-token":
            return UserContext(
                user_id="admin-001",
                username="admin",
                roles={"admin"},
                permissions={
                    "database.read",
                    "infrastructure.read",
                    "kubernetes.read",
                    "capacity.read",
                    "audit.read",
                },
            )

        return UserContext(
            user_id="user-001",
            username="engineer",
            roles={"database_engineer"},
            permissions={"database.read"},
        )


app.state.authentication_service = DummyAuthenticationService()

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_audit_events():
    app.state.orchestrator.audit_service.clear()
    yield
    app.state.orchestrator.audit_service.clear()


def add_audit_event(
    user_id: str,
    username: str,
    roles: frozenset[str],
    tool_name: str,
    permission: str,
    status: str,
    request: dict | None = None,
    timestamp: datetime | None = None,
):
    event = AuditEvent(
        user_id=user_id,
        username=username,
        roles=roles,
        tool_name=tool_name,
        permission=permission,
        request=request or {},
        status=status,
        timestamp=timestamp,
    )

    app.state.orchestrator.audit_service.record(event)


def test_health_endpoint_is_public():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_requires_authentication():
    response = client.post(
        "/api/v1/chat",
        json={"question": "Check database health"},
    )

    assert response.status_code == 401


def test_chat_endpoint_rejects_invalid_bearer_token():
    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": "Bearer invalid-token"},
        json={"question": "Check database health"},
    )

    assert response.status_code == 401


def test_chat_endpoint_accepts_authenticated_request():
    app.state.orchestrator.process = AsyncMock(
        return_value={"answer": "Database is healthy."}
    )

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"question": "Check database health"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Database is healthy."
    }

    app.state.orchestrator.process.assert_awaited_once_with(
        "Check database health",
        user_context=UserContext(
            user_id="user-001",
            username="engineer",
            roles={"database_engineer"},
            permissions={"database.read"},
        ),
    )


# --------------------------------------------------
# Audit API authentication and authorization tests
# --------------------------------------------------


def test_audit_endpoint_requires_authentication():
    response = client.get("/api/v1/audit")

    assert response.status_code == 401


def test_database_engineer_cannot_access_audit_endpoint():
    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Permission denied: audit.read"
    )


@pytest.mark.parametrize(
    "token",
    ["platform-token", "admin-token"],
)
def test_authorized_roles_can_access_audit_endpoint(token):
    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 50,
        "offset": 0,
    }


# --------------------------------------------------
# Audit API event retrieval tests
# --------------------------------------------------


def test_audit_endpoint_returns_recorded_events():
    add_audit_event(
        user_id="user-001",
        username="engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        status="success",
        request={"database": "dev"},
    )

    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == "user-001"
    assert data["items"][0]["tool_name"] == "postgresql"
    assert data["items"][0]["status"] == "success"


def test_audit_endpoint_returns_redacted_request_data():
    add_audit_event(
        user_id="user-001",
        username="engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        status="success",
        request={
            "database": "dev",
            "password": "[REDACTED]",
        },
    )

    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200

    returned_request = response.json()["items"][0]["request"]

    assert returned_request["database"] == "dev"
    assert returned_request["password"] == "[REDACTED]"


def test_audit_endpoint_does_not_return_error_details():
    event = AuditEvent(
        user_id="user-001",
        username="engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        request={},
        status="error",
        error="Internal connection details",
    )

    app.state.orchestrator.audit_service.record(event)

    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200

    returned_event = response.json()["items"][0]

    assert returned_event["status"] == "error"
    assert "error" not in returned_event


# --------------------------------------------------
# Audit API filtering tests
# --------------------------------------------------


def test_audit_endpoint_filters_by_user_id():
    add_audit_event(
        user_id="user-001",
        username="engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        status="success",
    )

    add_audit_event(
        user_id="user-002",
        username="engineer-two",
        roles=frozenset({"database_engineer"}),
        tool_name="mysql",
        permission="database.read",
        status="success",
    )

    response = client.get(
        "/api/v1/audit",
        params={"user_id": "user-001"},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["user_id"] == "user-001"


def test_audit_endpoint_filters_by_tool_name():
    add_audit_event(
        user_id="user-001",
        username="engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        status="success",
    )

    add_audit_event(
        user_id="user-002",
        username="engineer-two",
        roles=frozenset({"database_engineer"}),
        tool_name="mysql",
        permission="database.read",
        status="success",
    )

    response = client.get(
        "/api/v1/audit",
        params={"tool_name": "mysql"},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["tool_name"] == "mysql"


def test_audit_endpoint_filters_by_status():
    for status in ("success", "denied", "error"):
        add_audit_event(
            user_id="user-001",
            username="engineer",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            status=status,
        )

    response = client.get(
        "/api/v1/audit",
        params={"status": "denied"},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "denied"


def test_audit_endpoint_supports_combined_filters():
    add_audit_event(
        user_id="user-001",
        username="engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        status="success",
    )

    add_audit_event(
        user_id="user-001",
        username="engineer",
        roles=frozenset({"database_engineer"}),
        tool_name="mysql",
        permission="database.read",
        status="denied",
    )

    add_audit_event(
        user_id="user-002",
        username="engineer-two",
        roles=frozenset({"database_engineer"}),
        tool_name="postgresql",
        permission="database.read",
        status="success",
    )

    response = client.get(
        "/api/v1/audit",
        params={
            "user_id": "user-001",
            "tool_name": "postgresql",
            "status": "success",
        },
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["user_id"] == "user-001"
    assert response.json()["items"][0]["tool_name"] == "postgresql"


# --------------------------------------------------
# Audit API pagination tests
# --------------------------------------------------


def test_audit_endpoint_supports_pagination():
    base_time = datetime(
        2026, 11, 1, 10, 0, tzinfo=timezone.utc
    )

    for index in range(5):
        add_audit_event(
            user_id=f"user-{index}",
            username=f"engineer-{index}",
            roles=frozenset({"database_engineer"}),
            tool_name="postgresql",
            permission="database.read",
            status="success",
            timestamp=base_time + timedelta(minutes=index),
        )

    response = client.get(
        "/api/v1/audit",
        params={"limit": 2, "offset": 1},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["items"]) == 2

    # Events should be ordered newest first.
    assert data["items"][0]["user_id"] == "user-3"
    assert data["items"][1]["user_id"] == "user-2"


def test_audit_endpoint_rejects_limit_above_maximum():
    response = client.get(
        "/api/v1/audit",
        params={"limit": 201},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 422


def test_audit_endpoint_rejects_negative_offset():
    response = client.get(
        "/api/v1/audit",
        params={"offset": -1},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 422


# --------------------------------------------------
# Audit API validation tests
# --------------------------------------------------


def test_audit_endpoint_rejects_invalid_status():
    response = client.get(
        "/api/v1/audit",
        params={"status": "unknown"},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 422


def test_audit_endpoint_rejects_start_time_after_end_time():
    response = client.get(
        "/api/v1/audit",
        params={
            "start_time": "2026-11-02T12:00:00Z",
            "end_time": "2026-11-01T12:00:00Z",
        },
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 422


def test_audit_endpoint_rejects_timezone_naive_start_time():
    response = client.get(
        "/api/v1/audit",
        params={"start_time": "2026-11-01T12:00:00"},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 422


def test_audit_endpoint_rejects_timezone_naive_end_time():
    response = client.get(
        "/api/v1/audit",
        params={"end_time": "2026-11-01T12:00:00"},
        headers={"Authorization": "Bearer platform-token"},
    )

    assert response.status_code == 422


# --------------------------------------------------
# Keycloak startup test
# --------------------------------------------------


def test_application_startup_initializes_keycloak_authentication(
    monkeypatch,
):
    monkeypatch.setenv(
        "KEYCLOAK_SERVER_URL",
        "https://keycloak.example.com",
    )
    monkeypatch.setenv(
        "KEYCLOAK_REALM",
        "infradb",
    )
    monkeypatch.setenv(
        "KEYCLOAK_CLIENT_ID",
        "infradb-assist",
    )

    original_authentication_service = (
        app.state.authentication_service
    )

    try:
        with TestClient(app):
            assert isinstance(
                app.state.authentication_service,
                JWTAuthenticationService,
            )
    finally:
        app.state.authentication_service = (
            original_authentication_service
        )
