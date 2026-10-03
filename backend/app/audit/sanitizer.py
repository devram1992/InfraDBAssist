from collections.abc import Mapping
from typing import Any


class AuditSanitizer:
    """
    Sanitizes audit request data before it is persisted.

    Sensitive fields are replaced with [REDACTED].
    Nested dictionaries and lists are handled recursively.
    """

    REDACTED = "[REDACTED]"

    SENSITIVE_FIELDS = frozenset(
        {
            "password",
            "token",
            "access_token",
            "refresh_token",
            "client_secret",
            "secret",
            "api_key",
            "authorization",
        }
    )

    def sanitize(self, value: Any) -> Any:
        """
        Return a sanitized copy of the supplied value.

        The original object is never modified.
        """
        if isinstance(value, Mapping):
            return {
                key: (
                    self.REDACTED
                    if isinstance(key, str)
                    and key.lower() in self.SENSITIVE_FIELDS
                    else self.sanitize(item)
                )
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [self.sanitize(item) for item in value]

        if isinstance(value, tuple):
            return tuple(self.sanitize(item) for item in value)

        if isinstance(value, set):
            return {self.sanitize(item) for item in value}

        return value
