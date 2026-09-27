from backend.app.auth.role_permissions import (
    RolePermissionMapper,
)


def test_database_engineer_gets_database_permission():
    mapper = RolePermissionMapper()

    permissions = mapper.get_permissions(
        {"database_engineer"}
    )

    assert permissions == {
        "database.read",
    }


def test_platform_engineer_gets_all_read_permissions():
    mapper = RolePermissionMapper()

    permissions = mapper.get_permissions(
        {"platform_engineer"}
    )

    assert permissions == {
        "database.read",
        "infrastructure.read",
        "kubernetes.read",
        "capacity.read",
    }


def test_multiple_roles_combine_permissions():
    mapper = RolePermissionMapper()

    permissions = mapper.get_permissions(
        {
            "database_engineer",
            "kubernetes_engineer",
        }
    )

    assert permissions == {
        "database.read",
        "kubernetes.read",
    }


def test_unknown_role_gets_no_permissions():
    mapper = RolePermissionMapper()

    permissions = mapper.get_permissions(
        {"unknown_role"}
    )

    assert permissions == set()


def test_empty_roles_get_no_permissions():
    mapper = RolePermissionMapper()

    permissions = mapper.get_permissions(
        set()
    )

    assert permissions == set()


def test_roles_must_be_a_set():
    mapper = RolePermissionMapper()

    try:
        mapper.get_permissions(
            ["database_engineer"]
        )
    except ValueError as exc:
        assert str(exc) == "roles must be a set."
    else:
        raise AssertionError(
            "Expected ValueError"
        )
