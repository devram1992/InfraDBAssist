import importlib

from backend.app.config import settings as settings_module


def test_oracle_default_settings():
    settings = settings_module.Settings

    assert settings.oracle_host == ""
    assert settings.oracle_port == 1521
    assert settings.oracle_service == ""
    assert settings.oracle_username == ""
    assert settings.oracle_password == ""
    assert settings.oracle_connect_timeout == 10
    assert settings.oracle_query_timeout == 30


def test_oracle_environment_settings(monkeypatch):
    monkeypatch.setenv(
        "INFRADB_ORACLE_HOST",
        "oracle-dev.example.local",
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_PORT",
        "1522",
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_SERVICE",
        "DEVDB",
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_USERNAME",
        "infradb_readonly",
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_PASSWORD",
        "test-password",
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_CONNECT_TIMEOUT",
        "15",
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_QUERY_TIMEOUT",
        "45",
    )

    importlib.reload(settings_module)

    settings = settings_module.Settings

    assert settings.oracle_host == "oracle-dev.example.local"
    assert settings.oracle_port == 1522
    assert settings.oracle_service == "DEVDB"
    assert settings.oracle_username == "infradb_readonly"
    assert settings.oracle_password == "test-password"
    assert settings.oracle_connect_timeout == 15
    assert settings.oracle_query_timeout == 45