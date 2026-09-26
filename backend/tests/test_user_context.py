import pytest

from backend.app.auth.user_context import UserContext


def test_user_context_has_permission():
    context = UserContext(
        user_id="user-001",
        username="engineer",
        roles={"database_engineer"},
        permissions={
            "database.read",
            "infrastructure.read",
        },
    )

    assert context.has_permission(
        "database.read"
    )


def test_user_context_denies_missing_permission():
    context = UserContext(
        user_id="user-001",
        username="engineer",
        roles={"database_engineer"},
        permissions={
            "database.read",
        },
    )

    assert not context.has_permission(
        "kubernetes.read"
    )


def test_user_context_denies_empty_permission():
    context = UserContext(
        user_id="user-001",
        username="engineer",
    )

    assert not context.has_permission("")


def test_user_context_defaults_are_empty():
    context = UserContext(
        user_id="user-001",
        username="engineer",
    )

    assert context.roles == set()
    assert context.permissions == set()
