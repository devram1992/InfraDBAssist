from backend.app.tools.base import Tool


class LinuxTool(Tool):
    name = "linux"
    description = "Read-only Linux server diagnostics"
    permission = "infrastructure.read"
    read_only = True

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "server": request.get("server", "UNKNOWN"),
                "cpu_usage": "35%",
                "memory_usage": "62%",
                "disk_usage": "68%",
                "message": "Mock Linux response"
            }
        }