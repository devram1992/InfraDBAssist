from backend.app.tools.base import Tool


class OpenShiftTool(Tool):
    name = "openshift"
    description = "Read-only OpenShift cluster diagnostics"
    permission = "infrastructure.read"
    read_only = True

    parameters = {
        "cluster": {
            "type": "string",
            "description": "OpenShift cluster name",
            "required": True,
        }
    }

    def build_request(self, **kwargs) -> dict:
        """
        Build an OpenShift cluster request.
        """

        return {
            "cluster": kwargs.get("cluster", "OCP-PROD")
        }

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "cluster": request.get("cluster", "UNKNOWN"),
                "status": "HEALTHY",
                "nodes": 4,
                "pods": 86,
                "message": "Mock OpenShift response"
            }
        }