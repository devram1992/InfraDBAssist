from backend.app.tools.registry import ToolRegistry

from backend.app.ai.ollamaclient import OllamaClient

from backend.app.rag.service import RAGService

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

        self.rag = RAGService()

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

        if not question or not question.strip():
            raise ValueError("Question must not be empty.")

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

5. Extract parameters explicitly provided by the engineer.

6. Use the exact parameter names defined by the selected tool.

7. Do not invent parameter values.

8. If a parameter is not explicitly provided, omit it.

9. The selected tool may apply its own safe default for omitted parameters.

10. Do not select a tool only because a parameter is missing if the tool
    can safely handle the missing parameter using its own default.

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
        Execute a registered tool using the supplied parameters.
        """

        tool = self.tool_registry.get(tool_name)

        if tool is None:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}",
            }

        if parameters is None:
            parameters = {}

        if not isinstance(parameters, dict):
            return {
                "status": "error",
                "error": "Tool parameters must be a dictionary.",
            }

        try:
            request = tool.build_request(**parameters)
            tool.validate_request(request)

            result = await tool.execute(request)

            return result

        except ValueError as exc:
            return {
                "status": "error",
                "error": str(exc),
            }

        except Exception as exc:
            return {
                "status": "error",
                "error": f"Tool execution failed: {exc}",
            }

    async def search_knowledge(
        self,
        question: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search internal knowledge using the RAG service.
        """

        try:
            return await self.rag.search(
                question=question,
                limit=limit,
            )

        except Exception:
            return []

    async def generate_answer(
        self,
        question: str,
        tool_name: str,
        tool_result: dict,
        knowledge_results: list[dict],
    ) -> str:
        """
        Generate a grounded answer using only tool results
        and relevant internal knowledge.
        """

        knowledge_context = "\n\n".join(
            [
                (
                    f"Knowledge Document: {item['title']}\n"
                    f"Source Type: {item['source_type']}\n"
                    f"Similarity: {item['similarity']:.4f}\n"
                    f"Content:\n{item['content']}"
                )
                for item in knowledge_results
            ]
        )

        if not knowledge_context:
            knowledge_context = "No relevant internal knowledge was found."

        prompt = f"""
You are InfraDB Assist, an AI assistant for Infrastructure
and Database Engineering.

Answer the engineer's question using the available evidence below.

Engineer question:

{question}

Tool used:

{tool_name}

Tool result:

{tool_result}

Relevant internal knowledge:

{knowledge_context}

Rules:

1. Answer using ONLY the information contained in the
   Tool result and Relevant internal knowledge sections.

2. Do not add technical facts, commands, views, metrics,
   procedures, examples, or recommendations from your
   general model knowledge.

3. If a technical detail is not present in the supplied
   evidence, do not introduce it.

4. Use the tool result as the primary source for current
   system state.

5. Use internal knowledge only for documented procedures,
   troubleshooting guidance, context, and recommendations.

6. Clearly distinguish current system findings from
   documented internal guidance.

7. If the available evidence does not contain the answer,
   explicitly say that the available internal knowledge
   does not provide that information.

8. Do not expand, reinterpret, or supplement internal
   procedures with external or general knowledge.

9. Keep the response concise and technical.

10. Do not mention internal implementation details such as
    embeddings, vector databases, RAG, prompts, or orchestration.

Answer:
"""

        return await self.llm.generate(prompt)

    async def process(self, question: str) -> dict:
        """
        Complete orchestration flow:

        Question
            ↓
        Tool Selection
            ↓
        Tool Execution
            ↓
        Knowledge Search
            ↓
        Grounded Answer
        """

        selected = await self.select_tool(question)

        tool_name = None
        parameters = {}
        tool_result = None

        if selected:
            tool_name = selected["tool"]
            parameters = selected["parameters"]

            tool_result = await self.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
            )

        knowledge_results = await self.search_knowledge(
            question=question,
        )

        answer_tool_name = (
            tool_name
            if tool_name
            else "knowledge_only"
        )

        answer_tool_result = (
            tool_result
            if tool_result is not None
            else {}
        )

        answer = await self.generate_answer(
            question=question,
            tool_name=answer_tool_name,
            tool_result=answer_tool_result,
            knowledge_results=knowledge_results,
        )

        return {
            "status": "success",
            "question": question,
            "selected_tool": tool_name,
            "parameters": parameters,
            "tool_result": tool_result,
            "knowledge_results": knowledge_results,
            "answer": answer,
        }