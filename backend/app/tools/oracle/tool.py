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
        return {
            "database": kwargs.get("database", "PRODDB")
        }

    async def execute(self, request: dict) -> dict:
        """
        Check the current Oracle instance state using
        a read-only database query.
        """
        database = request.get("database", "UNKNOWN")

        await self.connection.connect()

        try:
            rows = await self.connection.execute(
                "SELECT status FROM v$instance"
            )

            state = (
                rows[0]["status"]
                if rows
                else "UNKNOWN"
            )

            return {
                "tool": self.name,
                "status": "success",
                "database": database,
                "state": state,
            }

        finally:
            await self.connection.disconnect()
