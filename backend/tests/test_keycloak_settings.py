from backend.app.auth.keycloak_settings import load_keycloak_config


def test_load_keycloak_config(monkeypatch):
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
    monkeypatch.setenv(
        "KEYCLOAK_CLIENT_SECRET",
        "secret",
    )

    config = load_keycloak_config()

    assert config.server_url == "https://keycloak.example.com"
    assert config.realm == "infradb"
    assert config.client_id == "infradb-assist"
    assert config.client_secret == "secret"


def test_load_keycloak_config_rejects_missing_required_values(monkeypatch):
    monkeypatch.delenv("KEYCLOAK_SERVER_URL", raising=False)
    monkeypatch.delenv("KEYCLOAK_REALM", raising=False)
    monkeypatch.delenv("KEYCLOAK_CLIENT_ID", raising=False)

    try:
        load_keycloak_config()
        assert False
    except ValueError as exc:
        assert str(exc) == "server_url must not be empty."
