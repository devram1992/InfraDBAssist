from backend.app.tools.registry import ToolRegistry
from backend.app.ai.ollamaclient import OllamaClient

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
        self.llm = OllamaClient()

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

    async def select_tool(self, question: str) -> dict | None:
        """
        Use the local LLM to select the most appropriate tool
        and extract the parameters required by that tool.
        """

        tools = self.tool_registry.get_tool_metadata()

        tool_list = "\n".join(
            [
                (
                    f"- {tool['name']}: {tool['description']}\n"
                    f"  Permission: {tool['permission']}\n"
                    f"  Read-only: {tool['read_only']}\n"
                    f"  Parameters: {tool['parameters']}"
                )
                for tool in tools
            ]
        )

        prompt = f"""
You are the tool-selection engine for InfraDB Assist.

Your job is to select exactly ONE tool for the engineer's question
and extract the parameters explicitly provided in the question.

Available tools:

{tool_list}

Return ONLY valid JSON using this exact structure:

{{
    "tool": "tool_name",
    "parameters": {{}}
}}

Rules:
1. The tool must be one of the available tools.
2. Return ONLY valid JSON.
3. Do not include markdown.
4. Do not include explanations.
5. Extract only parameters explicitly provided by the engineer.
6. Use the exact parameter names defined by the selected tool.
7. Do not invent parameter values.
8. If a parameter is not explicitly provided, do not create a value for it.
9. If no tool is suitable, return:
   {{"tool": "NONE", "parameters": {{}}}}

Engineer question:
{question}
"""

        try:
            result = await self.llm.generate_json(prompt)

        except ValueError:
            return None

        if not isinstance(result, dict):
            return None

        tool_name = result.get("tool")
        parameters = result.get("parameters", {})

        if tool_name == "NONE":
            return None

        if not isinstance(tool_name, str):
            return None

        if not self.tool_registry.has(tool_name):
            return None

        if not isinstance(parameters, dict):
            return None

        return {
            "tool": tool_name,
            "parameters": parameters,
        }

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict | None = None,
    ) -> dict:
        """
        Validate and execute a registered tool
        using the parameters selected by the LLM.
        """

        if not self.tool_registry.has(tool_name):
            return {
                "status": "error",
                "message": f"Tool not registered: {tool_name}",
            }

        tool = self.tool_registry.get(tool_name)

        try:
            parameters = parameters or {}

            request = tool.build_request(**parameters)

            tool.validate_request(request)

            return await tool.execute(request)

        except ValueError as exc:
            return {
                "status": "error",
                "message": f"Tool request validation failed: {exc}",
            }

        except Exception as exc:
            return {
                "status": "error",
                "message": f"Tool execution failed: {exc}",
            }

    async def generate_answer(
        self,
        question: str,
        tool_name: str,
        tool_result: dict,
    ) -> str:
        """
        Use the local LLM to convert the tool result
        into an engineer-friendly answer.
        """

        prompt = f"""
You are InfraDB Assist, an AI assistant for Infrastructure
and Database Engineering.

Answer the engineer's question using ONLY the information
provided by the tool result.

Engineer question:
{question}

Tool used:
{tool_name}

Tool result:
{tool_result}

Rules:
1. Do not invent information.
2. Do not assume facts that are not present in the tool result.
3. Clearly state the important findings.
4. Keep the response concise and technical.
5. If the data is insufficient to answer the question,
   clearly say that more information is required.
"""

        return await self.llm.generate(prompt)

    async def process(self, question: str) -> dict:
        """
        Process an engineer question.
        """

        tool_selection = await self.select_tool(question)

        if not tool_selection:
            return {
                "question": question,
                "status": "no_tool_selected",
                "message": "No suitable tool found.",
                "available_tools": self.tool_registry.get_tool_metadata(),
            }

        tool_name = tool_selection["tool"]
        parameters = tool_selection["parameters"]

        result = await self.execute_tool(
            tool_name,
            parameters,
        )

        if result.get("status") == "error":
            return {
                "question": question,
                "selected_tool": tool_name,
                "parameters": parameters,
                "status": "error",
                "message": result.get(
                    "message",
                    "Tool execution failed.",
                ),
            }

        answer = await self.generate_answer(
            question,
            tool_name,
            result,
        )

        return {
            "question": question,
            "selected_tool": tool_name,
            "parameters": parameters,
            "status": "success",
            "answer": answer,
            "tool_result": result,
        }