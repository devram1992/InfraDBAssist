from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.app.auth.authentication import (
    AuthenticationService,
)
from backend.app.auth.user_context import UserContext
from backend.app.main import app


class DummyAuthenticationService(
    AuthenticationService
):
    async def authenticate(
        self,
        credentials: dict,
    ) -> UserContext:
        token = credentials.get("token")

        if token == "invalid-token":
            raise ValueError(
                "Invalid JWT"
            )

        return UserContext(
            user_id="user-001",
            username="engineer",
            roles={
                "database_engineer",
            },
            permissions={
                "database.read",
            },
        )


app.state.authentication_service = (
    DummyAuthenticationService()
)

client = TestClient(app)


def test_health_endpoint_is_public():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
    }


def test_chat_endpoint_requires_authentication():
    response = client.post(
        "/api/v1/chat",
        json={
            "question": "Check database health",
        },
    )

    assert response.status_code == 401


def test_chat_endpoint_rejects_invalid_bearer_token():
    response = client.post(
        "/api/v1/chat",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "question": "Check database health",
        },
    )

    assert response.status_code == 401


def test_chat_endpoint_accepts_authenticated_request():
    app.state.orchestrator.process = AsyncMock(
        return_value={
            "answer": "Database is healthy.",
        }
    )

    response = client.post(
        "/api/v1/chat",
        headers={
            "Authorization": "Bearer valid-token",
        },
        json={
            "question": "Check database health",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "answer": "Database is healthy.",
    }

    app.state.orchestrator.process.assert_awaited_once_with(
        "Check database health",
        user_context=UserContext(
            user_id="user-001",
            username="engineer",
            roles={
                "database_engineer",
            },
            permissions={
                "database.read",
            },
        ),
    )

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

    from backend.app.auth.jwt_authentication import (
        JWTAuthenticationService,
    )

    with TestClient(app):
        assert isinstance(
            app.state.authentication_service,
            JWTAuthenticationService,
        )
