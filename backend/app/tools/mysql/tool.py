from backend.app.tools.base import Tool


class MySQLTool(Tool):
    name = "mysql_database"
    description = "Read-only MySQL database diagnostics"
    permission = "database.read"
    read_only = True

    def build_request(self) -> dict:
        return {
            "database": "MYSQLDB"
        }

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "database": request.get("database", "UNKNOWN"),
                "status": "UP",
                "connections": 28,
                "message": "Mock MySQL response"
            }
        }