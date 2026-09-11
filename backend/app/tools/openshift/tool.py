from backend.app.tools.base import Tool


class OpenShiftTool(Tool):
    name = "openshift"
    description = "Read-only OpenShift cluster diagnostics"
    permission = "infrastructure.read"
    read_only = True

    def build_request(self) -> dict:
        return {
            "cluster": "OCP-PROD"
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