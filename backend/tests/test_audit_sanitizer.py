from backend.app.audit.sanitizer import AuditSanitizer


def test_sanitizer_preserves_normal_fields():
    sanitizer = AuditSanitizer()

    request = {
        "action": "health",
        "database": "customer_db",
    }

    result = sanitizer.sanitize(request)

    assert result == request


def test_sanitizer_redacts_password():
    sanitizer = AuditSanitizer()

    request = {
        "username": "db-user",
        "password": "super-secret",
    }

    result = sanitizer.sanitize(request)

    assert result["username"] == "db-user"
    assert result["password"] == "[REDACTED]"


def test_sanitizer_redacts_sensitive_fields_case_insensitively():
    sanitizer = AuditSanitizer()

    request = {
        "PASSWORD": "secret-1",
        "Api_Key": "secret-2",
        "Authorization": "Bearer secret-3",
    }

    result = sanitizer.sanitize(request)

    assert result["PASSWORD"] == "[REDACTED]"
    assert result["Api_Key"] == "[REDACTED]"
    assert result["Authorization"] == "[REDACTED]"


def test_sanitizer_redacts_nested_dictionary():
    sanitizer = AuditSanitizer()

    request = {
        "connection": {
            "host": "db.example",
            "credentials": {
                "username": "db-user",
                "password": "super-secret",
            },
        }
    }

    result = sanitizer.sanitize(request)

    assert result["connection"]["host"] == "db.example"
    assert (
        result["connection"]["credentials"]["password"]
        == "[REDACTED]"
    )


def test_sanitizer_redacts_sensitive_values_inside_lists():
    sanitizer = AuditSanitizer()

    request = {
        "connections": [
            {
                "host": "db01",
                "token": "token-1",
            },
            {
                "host": "db02",
                "token": "token-2",
            },
        ]
    }

    result = sanitizer.sanitize(request)

    assert result["connections"][0]["host"] == "db01"
    assert result["connections"][0]["token"] == "[REDACTED]"
    assert result["connections"][1]["token"] == "[REDACTED]"


def test_sanitizer_does_not_modify_original_request():
    sanitizer = AuditSanitizer()

    request = {
        "password": "super-secret",
        "nested": {
            "token": "token-value",
        },
    }

    result = sanitizer.sanitize(request)

    assert request["password"] == "super-secret"
    assert request["nested"]["token"] == "token-value"
    assert result["password"] == "[REDACTED]"
    assert result["nested"]["token"] == "[REDACTED]"


def test_sanitizer_preserves_tuple_structure():
    sanitizer = AuditSanitizer()

    request = (
        {"password": "secret"},
        {"action": "health"},
    )

    result = sanitizer.sanitize(request)

    assert isinstance(result, tuple)
    assert result[0]["password"] == "[REDACTED]"
    assert result[1]["action"] == "health"
