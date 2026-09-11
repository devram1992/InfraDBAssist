from backend.app.tools.base import Tool


class OracleTool(Tool):
    name = "oracle_database"
    description = "Read-only Oracle database diagnostics"
    permission = "database.read"
    read_only = True

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "database": request.get("database", "UNKNOWN"),
                "status": "OPEN",
                "message": "Mock Oracle response"
            }
        }

    