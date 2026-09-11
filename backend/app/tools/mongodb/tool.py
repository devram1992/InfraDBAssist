from backend.app.tools.base import Tool


class MongoDBTool(Tool):
    name = "mongodb_database"
    description = "Read-only MongoDB database diagnostics"
    permission = "database.read"
    read_only = True

    def build_request(self) -> dict:
        return {
            "database": "MONGODB"
        }

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "database": request.get("database", "UNKNOWN"),
                "status": "UP",
                "connections": 15,
                "message": "Mock MongoDB response"
            }
        }