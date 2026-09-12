from backend.app.tools.base import Tool


class MongoDBTool(Tool):
    name = "mongodb_database"
    description = "Read-only MongoDB database diagnostics"
    permission = "database.read"
    read_only = True

    parameters = {
        "database": {
            "type": "string",
            "description": "MongoDB database name",
            "required": True,
        }
    }

    def build_request(self, **kwargs) -> dict:
        """
        Build a MongoDB database request.
        """

        return {
            "database": kwargs.get("database", "MONGODB")
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