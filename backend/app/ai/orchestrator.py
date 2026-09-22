from __future__ import annotations

import re

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
from backend.app.tools.capacity.tool import CapacityForecastTool


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
        self.tool_registry.register(CapacityForecastTool())

    async def select_tool(
        self,
        question: str,
    ) -> dict | None:
        """
        Use the local LLM to select the most appropriate tool
        and extract the parameters required by that tool.
        """

        if not question or not question.strip():
            raise ValueError(
                "Question must not be empty."
            )

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

Your job is to determine whether the engineer's question
requires a live system tool or can be answered from internal
knowledge.

If a live system tool is required, select exactly ONE tool
and extract the parameters explicitly provided in the question.

Available tools:

{tool_list}

Return ONLY valid JSON using this exact structure:

{{
    "tool": "tool_name",
    "parameters": {{}}
}}

Rules:

1. Select a tool when the engineer is asking to inspect,
   check, diagnose, retrieve, verify, analyze, or forecast
   a specific system, database, server, cluster, or infrastructure
   environment using available tool data.

2. Do NOT select a tool when the engineer is asking:
   - how to perform a procedure
   - how to verify something
   - for a documented procedure
   - for an explanation
   - for troubleshooting guidance
   - for general technical information
   - for a runbook, SOP, RCA, or other internal knowledge

3. For knowledge, procedure, explanation, or troubleshooting
   questions, return:

   {{
       "tool": "NONE",
       "parameters": {{}}
   }}

4. If the question could be answered from internal documentation
   without inspecting a live system, return "NONE".

5. Select a database tool only when the question requires
   current database/system information.

6. Select an infrastructure tool only when the question requires
   current infrastructure/system information.

7. The tool must be one of the available tools or "NONE".

8. Return ONLY valid JSON.

9. Do not include markdown.

10. Do not include explanations.

11. Extract parameters explicitly provided by the engineer,
    and infer a parameter only when its value is unambiguously
    determined by the wording of the question.

12. Use the exact parameter names defined by the selected tool.

13. Do not invent parameter values.

14. If a parameter is not explicitly provided and cannot be
    unambiguously determined from the question, omit it.

15. The selected tool may apply its own safe default for omitted
    parameters.

16. Do not select a tool only because a parameter is missing if
    the tool can safely handle the missing parameter using its
    own default.

Capacity forecasting rules:

17. Select "capacity_forecast" when the engineer asks for:
    - capacity forecasting
    - future utilization
    - growth trend
    - projected capacity
    - projected storage usage
    - storage growth
    - future storage consumption
    - when a resource will reach a threshold
    - estimated threshold breach
    - expected utilization after a number of days

18. For "capacity_forecast":

    - target identifies the database/system.

    - resource identifies the capacity resource.

    - For Oracle tablespaces, use the canonical resource name
      without the word "tablespace".
      Example:
        "SYSTEM tablespace" -> "SYSTEM"
        "SYSAUX tablespace" -> "SYSAUX"

    - For storage, size, space consumed, storage growth,
      MB, GB, or "how much storage":
        metric = "used_mb"
        unit = "MB"

    - For utilization, percentage, %, or a threshold such as 99%:
        metric = "used_percent"
        unit = "percent"

    - For a capacity_forecast selection, ALWAYS return
      both "metric" and "unit" when the question makes
      the metric unambiguous.

    - threshold should only be extracted when explicitly
      provided in the question.

    - horizon_days should only be extracted when explicitly
      provided in the question.

    - Do not invent a target or resource.

19. Example:

Question:
"When will SYSTEM tablespace in FREEPDB1 reach 99%?"

Return:

{{
    "tool": "capacity_forecast",
    "parameters": {{
        "target": "FREEPDB1",
        "resource": "SYSTEM",
        "metric": "used_percent",
        "unit": "percent",
        "threshold": 99
    }}
}}

20. Example:

Question:
"How much storage will SYSTEM tablespace in FREEPDB1
use in the next 30 days?"

Return:

{{
    "tool": "capacity_forecast",
    "parameters": {{
        "target": "FREEPDB1",
        "resource": "SYSTEM",
        "metric": "used_mb",
        "unit": "MB",
        "horizon_days": 30
    }}
}}

Engineer question:

{question}
"""

        try:
            result = await self.llm.generate_json(
                prompt
            )
        except ValueError:
            return None

        if not isinstance(result, dict):
            return None

        tool_name = result.get("tool")
        parameters = result.get(
            "parameters",
            {},
        )

        if tool_name == "NONE":
            return None

        if not isinstance(tool_name, str):
            return None

        tool = self.tool_registry.get(
            tool_name
        )

        if tool is None:
            return None

        if not isinstance(parameters, dict):
            return None

        declared_parameters = tool.parameters

        unknown_parameters = (
            set(parameters)
            - set(declared_parameters)
        )

        if unknown_parameters:
            return None

        if tool_name == "capacity_forecast":
            parameters = (
                self._normalize_capacity_parameters(
                    question=question,
                    parameters=parameters,
                )
            )

        return {
            "tool": tool_name,
            "parameters": parameters,
        }

    @staticmethod
    def _normalize_capacity_parameters(
        question: str,
        parameters: dict,
    ) -> dict:
        """
        Normalize capacity forecast parameters.

        The LLM is responsible for intent selection, while this
        method enforces canonical values required by the
        capacity forecast tool.
        """

        normalized = dict(parameters)

        resource = normalized.get(
            "resource"
        )

        if isinstance(resource, str):
            resource = " ".join(
                resource.split()
            )

            resource = re.sub(
                r"\s+tablespace$",
                "",
                resource,
                flags=re.IGNORECASE,
            )

            resource = re.sub(
                r"\s+table\s+space$",
                "",
                resource,
                flags=re.IGNORECASE,
            )

            normalized["resource"] = (
                resource.strip()
            )

        question_lower = question.lower()

        metric = normalized.get(
            "metric"
        )

        unit = normalized.get(
            "unit"
        )

        # Derive metric only when the question clearly
        # identifies the required measurement.
        if not metric:
            threshold_requested = bool(
                normalized.get("threshold")
            ) or bool(
                re.search(
                    r"\d+(?:\.\d+)?\s*%",
                    question_lower,
                )
            )

            utilization_requested = any(
                phrase in question_lower
                for phrase in (
                    "utilization",
                    "utilisation",
                    "percentage",
                    "percent",
                    "usage %",
                    "used %",
                )
            )

            storage_requested = any(
                phrase in question_lower
                for phrase in (
                    "storage",
                    "storage usage",
                    "storage growth",
                    "space consumed",
                    "space usage",
                    "size",
                    "mb",
                    "gb",
                )
            )

            if (
                threshold_requested
                or utilization_requested
            ):
                metric = "used_percent"

            elif storage_requested:
                metric = "used_mb"

        if metric:
            normalized["metric"] = metric

        # Derive unit from metric when unambiguous.
        if not unit and metric:
            if metric == "used_mb":
                unit = "MB"

            elif metric == "used_percent":
                unit = "percent"

        if unit:
            normalized["unit"] = unit

        # Normalize common LLM unit variants.
        if isinstance(
            normalized.get("unit"),
            str,
        ):
            unit_lower = (
                normalized["unit"]
                .strip()
                .lower()
            )

            if unit_lower in {
                "%",
                "percent",
                "percentage",
            }:
                normalized["unit"] = "percent"

            elif unit_lower in {
                "mb",
                "megabyte",
                "megabytes",
            }:
                normalized["unit"] = "MB"

        # Normalize common metric variants.
        if isinstance(
            normalized.get("metric"),
            str,
        ):
            metric_lower = (
                normalized["metric"]
                .strip()
                .lower()
            )

            if metric_lower in {
                "used mb",
                "used_mb",
                "storage",
                "storage_mb",
                "storage_growth",
            }:
                normalized["metric"] = "used_mb"

            elif metric_lower in {
                "used percent",
                "used_percent",
                "utilization",
                "utilisation",
                "usage_percent",
            }:
                normalized["metric"] = (
                    "used_percent"
                )

        return normalized

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict | None = None,
    ) -> dict:
        """
        Execute a registered tool using the supplied parameters.
        """

        tool = self.tool_registry.get(
            tool_name
        )

        if tool is None:
            return {
                "status": "error",
                "error": (
                    f"Unknown tool: {tool_name}"
                ),
            }

        if parameters is None:
            parameters = {}

        if not isinstance(parameters, dict):
            return {
                "status": "error",
                "error": (
                    "Tool parameters must be "
                    "a dictionary."
                ),
            }

        try:
            request = tool.build_request(
                **parameters
            )

            tool.validate_request(
                request
            )

            result = await tool.execute(
                request
            )

            return result

        except ValueError as exc:
            return {
                "status": "error",
                "error": str(exc),
            }

        except Exception as exc:
            return {
                "status": "error",
                "error": (
                    f"Tool execution failed: {exc}"
                ),
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
            knowledge_context = (
                "No relevant internal knowledge was found."
            )

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

        return await self.llm.generate(
            prompt
        )

    async def process(
        self,
        question: str,
    ) -> dict:
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

        selected = await self.select_tool(
            question
        )

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

        knowledge_results = (
            await self.search_knowledge(
                question=question,
            )
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