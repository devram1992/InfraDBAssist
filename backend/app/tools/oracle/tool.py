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
            "required": False,
        },
        "action": {
            "type": "string",
            "description": "Oracle diagnostic action",
            "required": False,
            "allowed_values": [
                "health",
                "sessions",
                "tablespace",
            ],
        },
    }

    def __init__(
        self,
        connection: OracleConnection | None = None,
    ):
        self.connection = connection or OracleConnection()

    def build_request(self, **kwargs) -> dict:
        """
        Build an Oracle database diagnostic request.
        """

        database = kwargs.get("database")

        if not database:
            database = (
                Settings.oracle_service
                or "UNKNOWN"
            )

        action = kwargs.get(
            "action",
            "health",
        )

        if action not in {
            "health",
            "sessions",
            "tablespace",
        }:
            raise ValueError(
                "Unsupported Oracle diagnostic action."
            )

        return {
            "database": database,
            "action": action,
        }

    async def execute(self, request: dict) -> dict:
        """
        Execute a read-only Oracle diagnostic action.
        """

        database = request.get(
            "database",
            "UNKNOWN",
        )

        action = request.get(
            "action",
            "health",
        )

        await self.connection.connect()

        try:
            if action == "health":
                return await self._health(
                    database=database,
                )

            if action == "sessions":
                return await self._sessions(
                    database=database,
                )

            if action == "tablespace":
                return await self._tablespace(
                    database=database,
                )

            raise ValueError(
                "Unsupported Oracle diagnostic action."
            )

        finally:
            await self.connection.disconnect()

    async def _health(
        self,
        database: str,
    ) -> dict:
        """
        Collect the Oracle database health summary.
        """

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
            "action": "health",
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

    async def _sessions(
        self,
        database: str,
    ) -> dict:
        """
        Collect active user sessions.
        """

        rows = await self.connection.execute(
            """
            SELECT
                sid,
                serial#,
                username,
                status,
                event,
                machine,
                program
            FROM v$session
            WHERE type = 'USER'
            AND status = 'ACTIVE'
            ORDER BY sid
            FETCH FIRST 20 ROWS ONLY
            """
        )

        return {
            "tool": self.name,
            "status": "success",
            "database": database,
            "action": "sessions",
            "sessions": rows,
            "count": len(rows),
        }

    async def _tablespace(
        self,
        database: str,
    ) -> dict:
        """
        Collect Oracle tablespace capacity information.
        """

        rows = await self.connection.execute(
            """
            SELECT
                df.tablespace_name,
                ROUND(
                    SUM(df.bytes) / 1024 / 1024,
                    2
                ) AS total_mb,
                ROUND(
                    NVL(fs.free_mb, 0),
                    2
                ) AS free_mb
            FROM dba_data_files df
            LEFT JOIN (
                SELECT
                    tablespace_name,
                    SUM(bytes) / 1024 / 1024 AS free_mb
                FROM dba_free_space
                GROUP BY tablespace_name
            ) fs
                ON fs.tablespace_name =
                    df.tablespace_name
            GROUP BY
                df.tablespace_name,
                fs.free_mb
            ORDER BY
                df.tablespace_name
            """
        )

        tablespaces = []

        for row in rows:
            total_mb = float(
                row.get("total_mb", 0) or 0
            )

            free_mb = float(
                row.get("free_mb", 0) or 0
            )

            used_mb = max(
                total_mb - free_mb,
                0,
            )

            used_percent = (
                round(
                    (used_mb / total_mb) * 100,
                    2,
                )
                if total_mb > 0
                else 0.0
            )

            tablespaces.append(
                {
                    "tablespace_name": row.get(
                        "tablespace_name",
                        "UNKNOWN",
                    ),
                    "total_mb": total_mb,
                    "used_mb": round(
                        used_mb,
                        2,
                    ),
                    "free_mb": free_mb,
                    "used_percent": used_percent,
                }
            )

        return {
            "tool": self.name,
            "status": "success",
            "database": database,
            "action": "tablespace",
            "tablespaces": tablespaces,
            "count": len(tablespaces),
        }
