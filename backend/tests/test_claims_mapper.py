import pytest

from backend.app.auth.claims_mapper import ClaimsMapper
from backend.app.auth.user_context import UserContext


def test_claims_are_mapped_to_user_context():
    mapper = ClaimsMapper()

    context = mapper.to_user_context(
        {
            "sub": "user-001",
            "preferred_username": "engineer",
            "roles": [
                "database_engineer",
            ],
            "permissions": [
                "database.read",
            ],
        }
    )

    assert isinstance(
        context,
        UserContext,
    )

    assert context.user_id == "user-001"
    assert context.username == "engineer"
    assert context.roles == {
        "database_engineer",
    }
    assert context.permissions == {
        "database.read",
    }


def test_claims_without_roles_or_permissions_use_empty_sets():
    mapper = ClaimsMapper()

    context = mapper.to_user_context(
        {
            "sub": "user-002",
            "preferred_username": "engineer2",
        }
    )

    assert context.roles == set()
    assert context.permissions == set()


def test_missing_subject_is_rejected():
    mapper = ClaimsMapper()

    with pytest.raises(
        ValueError,
        match="missing required 'sub'",
    ):
        mapper.to_user_context(
            {
                "preferred_username": "engineer",
            }
        )


def test_missing_username_is_rejected():
    mapper = ClaimsMapper()

    with pytest.raises(
        ValueError,
        match="missing required 'preferred_username'",
    ):
        mapper.to_user_context(
            {
                "sub": "user-001",
            }
        )


def test_invalid_claims_are_rejected():
    mapper = ClaimsMapper()

    with pytest.raises(
        ValueError,
        match="Claims must be a dictionary",
    ):
        mapper.to_user_context("invalid")
def test_keycloak_realm_roles_are_mapped():

    mapper = ClaimsMapper()

    context = mapper.to_user_context(
        {
            "sub": "user-003",
            "preferred_username": "keycloak-user",
            "realm_access": {
                "roles": [
                    "database_engineer",
                    "platform_engineer",
                ],
            },
        }
    )

    assert context.user_id == "user-003"
    assert context.username == "keycloak-user"
    assert context.roles == {
        "database_engineer",
        "platform_engineer",
    }


def test_keycloak_client_roles_are_mapped():

    mapper = ClaimsMapper()

    context = mapper.to_user_context(
        {
            "sub": "user-004",
            "preferred_username": "keycloak-client-user",
            "resource_access": {
                "infradb-assist": {
                    "roles": [
                        "database_engineer",
                    ],
                },
            },
        }
    )

    assert context.user_id == "user-004"
    assert context.username == "keycloak-client-user"
    assert context.roles == {
        "database_engineer",
    }
