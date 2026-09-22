from backend.app.config.settings import Settings
from backend.app.integrations.databases.oracle import OracleConnection
from backend.app.tools.base import Tool


class OracleTool(Tool):
    name = "oracle_database"
    description = "Read-only Oracle database diagnostics"
    permission = "database.read"
    read_only = True

    parameters = {
        "database": {
            "type": "string",
            "description": "Oracle database name",
            "required": True,
        }
    }

    def __init__(
        self,
        connection: OracleConnection | None = None,
    ):
        self.connection = connection or OracleConnection()

    def build_request(self, **kwargs) -> dict:
        """
        Build an Oracle database request.
        """

        database = kwargs.get("database")

        if not database:
            database = (
                Settings.oracle_service
                or "UNKNOWN"
            )

        return {
            "database": database,
        }

    async def execute(self, request: dict) -> dict:
        """
        Collect a read-only Oracle database health summary.
        """

        database = request.get(
            "database",
            "UNKNOWN",
        )

        await self.connection.connect()

        try:
            instance_rows = await self.connection.execute(
                """
                SELECT
                    instance_name,
                    host_name,
                    status,
                    version
                FROM v$instance
                """
            )

            database_rows = await self.connection.execute(
                """
                SELECT
                    name,
                    open_mode,
                    database_role
                FROM v$database
                """
            )

            context_rows = await self.connection.execute(
                """
                SELECT
                    SYS_CONTEXT(
                        'USERENV',
                        'CON_NAME'
                    ) AS container_name,
                    SYS_CONTEXT(
                        'USERENV',
                        'DB_NAME'
                    ) AS db_name
                FROM dual
                """
            )

            instance = (
                instance_rows[0]
                if instance_rows
                else {}
            )

            database_info = (
                database_rows[0]
                if database_rows
                else {}
            )

            context = (
                context_rows[0]
                if context_rows
                else {}
            )

            state = instance.get(
                "status",
                "UNKNOWN",
            )

            return {
                "tool": self.name,
                "status": "success",
                "database": database,
                "state": state,
                "instance": {
                    "instance_name": instance.get(
                        "instance_name",
                        "UNKNOWN",
                    ),
                    "host_name": instance.get(
                        "host_name",
                        "UNKNOWN",
                    ),
                    "status": state,
                    "version": instance.get(
                        "version",
                        "UNKNOWN",
                    ),
                },
                "database_info": {
                    "name": database_info.get(
                        "name",
                        "UNKNOWN",
                    ),
                    "open_mode": database_info.get(
                        "open_mode",
                        "UNKNOWN",
                    ),
                    "database_role": database_info.get(
                        "database_role",
                        "UNKNOWN",
                    ),
                },
                "container": {
                    "container_name": context.get(
                        "container_name",
                        "UNKNOWN",
                    ),
                    "db_name": context.get(
                        "db_name",
                        "UNKNOWN",
                    ),
                },
            }

        finally:
            await self.connection.disconnect()