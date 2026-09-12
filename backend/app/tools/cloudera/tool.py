from backend.app.tools.base import Tool


class ClouderaTool(Tool):
    name = "cloudera_platform"
    description = "Read-only Cloudera platform diagnostics"
    permission = "database.read"
    read_only = True

    parameters = {
        "cluster": {
            "type": "string",
            "description": "Cloudera cluster name",
            "required": True,
        }
    }

    def build_request(self, **kwargs) -> dict:
        """
        Build a Cloudera platform request.
        """

        return {
            "cluster": kwargs.get("cluster", "CLD-PROD")
        }

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "cluster": request.get("cluster", "UNKNOWN"),
                "status": "HEALTHY",
                "services": "RUNNING",
                "message": "Mock Cloudera response"
            }
        }