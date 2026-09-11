from backend.app.tools.registry import ToolRegistry
from backend.app.tools.oracle.tool import OracleTool
from backend.app.tools.linux.tool import LinuxTool
from backend.app.tools.postgres.tool import PostgreSQLTool
from backend.app.tools.mysql.tool import MySQLTool
from backend.app.tools.mongodb.tool import MongoDBTool
from backend.app.tools.singlestore.tool import SingleStoreTool
from backend.app.tools.cloudera.tool import ClouderaTool
from backend.app.tools.kubernetes.tool import KubernetesTool
from backend.app.tools.openshift.tool import OpenShiftTool


class AIOrchestrator:

    def __init__(self):
        self.tool_registry = ToolRegistry()

        # Register available tools
        self.tool_registry.register(OracleTool())
        self.tool_registry.register(LinuxTool())
        self.tool_registry.register(PostgreSQLTool())
        self.tool_registry.register(MySQLTool())
        self.tool_registry.register(MongoDBTool())
        self.tool_registry.register(SingleStoreTool())
        self.tool_registry.register(ClouderaTool())
        self.tool_registry.register(KubernetesTool())
        self.tool_registry.register(OpenShiftTool())

    def select_tool(self, question: str) -> str | None:
        """
        Select the appropriate tool for the question.

        This is currently rule-based.
        It will later be replaced by local LLM-based tool selection.
        """
        question_lower = question.lower()

        if "oracle" in question_lower:
            return "oracle_database"

        elif "linux" in question_lower or "server" in question_lower:
            return "linux"

        elif "postgresql" in question_lower or "postgres" in question_lower:
            return "postgresql_database"

        elif "mysql" in question_lower:
            return "mysql_database"

        elif "mongodb" in question_lower or "mongo" in question_lower:
            return "mongodb_database"

        elif "singlestore" in question_lower or "single store" in question_lower:
            return "singlestore_database"

        elif "cloudera" in question_lower:
            return "cloudera_platform"

        elif "kubernetes" in question_lower or "k8s" in question_lower:
            return "kubernetes"

        elif "openshift" in question_lower or "open shift" in question_lower:
            return "openshift"

        return None

    async def execute_tool(self, tool_name: str) -> dict:
        """
        Validate and execute a registered tool.
        """
        if not self.tool_registry.has(tool_name):
            return {
                "status": "error",
                "message": f"Tool not registered: {tool_name}"
            }

        tool = self.tool_registry.get(tool_name)

        request = tool.build_request()

        return await tool.execute(request)

    async def process(self, question: str) -> dict:
        """
        Process an engineer question.
        """
        tool_name = self.select_tool(question)

        if not tool_name:
            return {
                "question": question,
                "status": "no_tool_selected",
                "message": "No suitable tool found.",
                "available_tools": self.tool_registry.get_tool_metadata()
            }

        result = await self.execute_tool(tool_name)

        if result.get("status") == "error":
            return {
                "question": question,
                "selected_tool": tool_name,
                "status": "error",
                "message": result.get("message", "Tool execution failed.")
            }

        return {
            "question": question,
            "selected_tool": tool_name,
            "status": "success",
            "tool_result": result
        }