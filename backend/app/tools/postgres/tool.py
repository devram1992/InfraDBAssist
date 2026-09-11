from backend.app.tools.base import Tool


class PostgreSQLTool(Tool):
    name = "postgresql_database"
    description = "Read-only PostgreSQL database diagnostics"
    permission = "database.read"
    read_only = True

    def build_request(self) -> dict:
        return {
            "database": "POSTGRESDB"
        }

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "database": request.get("database", "UNKNOWN"),
                "status": "UP",
                "connections": 42,
                "message": "Mock PostgreSQL response"
            }
        }