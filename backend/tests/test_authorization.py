import pytest

from backend.app.auth.authorization import AuthorizationService


def test_allows_matching_permission():
    auth = AuthorizationService()

    assert auth.is_allowed(
        user_permissions={"database.read"},
        required_permission="database.read",
    )


def test_denies_missing_permission():
    auth = AuthorizationService()

    assert not auth.is_allowed(
        user_permissions={"infrastructure.read"},
        required_permission="database.read",
    )


def test_allows_multiple_permissions():
    auth = AuthorizationService()

    assert auth.is_allowed(
        user_permissions={
            "database.read",
            "infrastructure.read",
        },
        required_permission="infrastructure.read",
    )


def test_empty_user_permissions_are_denied():
    auth = AuthorizationService()

    assert not auth.is_allowed(
        user_permissions=set(),
        required_permission="database.read",
    )


def test_empty_required_permission_is_denied():
    auth = AuthorizationService()

    assert not auth.is_allowed(
        user_permissions={"database.read"},
        required_permission="",
    )


def test_invalid_user_permissions_are_rejected():
    auth = AuthorizationService()

    with pytest.raises(ValueError):
        auth.is_allowed(
            user_permissions=None,
            required_permission="database.read",
        )
from backend.app.tools.base import Tool


class DummyTool(Tool):
    name = "dummy"
    description = "Dummy tool for authorization testing"
    permission = "database.read"
    read_only = True
    parameters = {}

    async def execute(self, request: dict) -> dict:
        return {"status": "executed"}


def test_authorization_matches_tool_permission():
    auth = AuthorizationService()
    tool = DummyTool()

    assert auth.is_allowed(
        user_permissions={"database.read"},
        required_permission=tool.permission,
    )


def test_authorization_denies_tool_permission():
    auth = AuthorizationService()
    tool = DummyTool()

    assert not auth.is_allowed(
        user_permissions={"infrastructure.read"},
        required_permission=tool.permission,
    )