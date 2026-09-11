from backend.app.tools.registry import ToolRegistry
from backend.app.tools.oracle.tool import OracleTool
from backend.app.tools.linux.tool import LinuxTool


class AIOrchestrator:

    def __init__(self):
        self.tool_registry = ToolRegistry()

        # Register available tools
        self.tool_registry.register(OracleTool())
        self.tool_registry.register(LinuxTool())

    async def process(self, question: str) -> dict:
        question_lower = question.lower()

        # Tool selection
        if "oracle" in question_lower:
            tool_name = "oracle_database"

        elif "linux" in question_lower or "server" in question_lower:
            tool_name = "linux"

        else:
            return {
                "question": question,
                "status": "no_tool_selected",
                "message": "No suitable tool found."
            }

        # Validate that the selected tool is registered
        if not self.tool_registry.has(tool_name):
            return {
                "question": question,
                "status": "error",
                "message": f"Tool not registered: {tool_name}"
            }

        # Get the selected tool
        tool = self.tool_registry.get(tool_name)

        # Execute selected tool
        if tool_name == "oracle_database":
            result = await tool.execute({
                "database": "PRODDB"
            })

        elif tool_name == "linux":
            result = await tool.execute({
                "server": "PROD-SERVER"
            })

        else:
            return {
                "question": question,
                "status": "error",
                "message": f"Unsupported tool: {tool_name}"
            }

        # Return structured result
        return {
            "question": question,
            "selected_tool": tool_name,
            "status": "success",
            "tool_result": result
        }