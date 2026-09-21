import oracledb

from backend.app.integrations.databases.base import DatabaseConnection
from backend.app.config.settings import Settings


class OracleConnection(DatabaseConnection):
    """
    Read-only Oracle database connection.
    """

    name = "oracle"
    read_only = True

    def __init__(self, config: dict | None = None):
        super().__init__(config or {})

        self.connection = None

        self.host = self.config.get(
            "host",
            Settings.oracle_host,
        )

        self.port = int(
            self.config.get(
                "port",
                Settings.oracle_port,
            )
        )

        self.service = self.config.get(
            "service",
            Settings.oracle_service,
        )

        self.username = self.config.get(
            "username",
            Settings.oracle_username,
        )

        self.password = self.config.get(
            "password",
            Settings.oracle_password,
        )

        self.connect_timeout = float(
            self.config.get(
                "connect_timeout",
                Settings.oracle_connect_timeout,
            )
        )

        self.query_timeout = float(
            self.config.get(
                "query_timeout",
                Settings.oracle_query_timeout,
            )
        )

    def _validate_config(self) -> None:
        if not self.host:
            raise ValueError("Oracle host is not configured.")

        if not self.service:
            raise ValueError("Oracle service is not configured.")

        if not self.username:
            raise ValueError("Oracle username is not configured.")

        if not self.password:
            raise ValueError("Oracle password is not configured.")

    async def connect(self) -> None:
        self._validate_config()

        dsn = oracledb.makedsn(
            self.host,
            self.port,
            service_name=self.service,
        )

        self.connection = oracledb.connect(
            user=self.username,
            password=self.password,
            dsn=dsn,
            tcp_connect_timeout=self.connect_timeout,
        )

    async def disconnect(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    async def execute(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> list[dict]:
        if self.connection is None:
            raise RuntimeError(
                "Oracle connection is not established."
            )

        if not query or not query.strip():
            raise ValueError(
                "Oracle query must not be empty."
            )

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                query,
                parameters or {},
            )

            columns = [
                column[0].lower()
                for column in cursor.description
            ]

            rows = cursor.fetchall()

            return [
                dict(zip(columns, row))
                for row in rows
            ]

        finally:
            cursor.close()

    async def health_check(self) -> dict:
        if self.connection is None:
            return {
                "status": "disconnected",
                "database": "oracle",
            }

        try:
            cursor = self.connection.cursor()

            try:
                cursor.execute("SELECT 1 FROM dual")
                cursor.fetchone()

                return {
                    "status": "healthy",
                    "database": "oracle",
                }

            finally:
                cursor.close()

        except Exception as exc:
            return {
                "status": "unhealthy",
                "database": "oracle",
                "error": str(exc),
            }
