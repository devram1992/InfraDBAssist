from backend.app.tools.base import Tool


class SingleStoreTool(Tool):
    name = "singlestore_database"
    description = "Read-only SingleStore database diagnostics"
    permission = "database.read"
    read_only = True

    def build_request(self) -> dict:
        return {
            "database": "SINGLESTOREDB"
        }

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "database": request.get("database", "UNKNOWN"),
                "status": "UP",
                "connections": 18,
                "message": "Mock SingleStore response"
            }
        }