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
from backend.app.auth.authorization import AuthorizationService
from backend.app.auth.user_context import UserContext
from backend.app.tools.executor import ToolExecutor


class AIOrchestrator:

    def __init__(self):
        self.tool_registry = ToolRegistry()

        self.llm = OllamaClient()
        self.rag = RAGService()

        # Authorization and controlled tool execution
        self.authorization = AuthorizationService()
        self.tool_executor = ToolExecutor(
            self.authorization
        )

        # Temporary POC user context.
        #
        # In the next phase, this context will be populated
        # from the authenticated user's RBAC identity.
        self.user_context = UserContext(
            user_id="poc-user",
            username="engineer",
            roles={"database_engineer"},
            permissions={
                "database.read",
                "infrastructure.read",
                "kubernetes.read",
                "capacity.read",
            },
        )

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

    # =============================================================
    # TOOL SELECTION
    # =============================================================

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

Kubernetes rules:

21. Select "kubernetes" when the engineer asks for CURRENT
    Kubernetes cluster information.

22. For "kubernetes", use these actions:

    - "health" when asking for overall cluster health,
      node health, or whether the cluster is healthy.

    - "nodes" when asking specifically about Kubernetes nodes,
      node status, readiness, versions, or runtime.

    - "pods" when asking for pods, pod status, or pod inventory.

    - "high_restart_pods" when asking about pods with high,
      excessive, or frequent restarts.

    - "pending_pods" when asking which pods are pending
      or stuck in Pending state.

    - "failed_pods" when asking which pods are failed.

    - "pod_details" when asking for details about a specific pod.

    - "logs" when asking for logs from a specific pod.

    - "events" when asking for Kubernetes events.

23. For "kubernetes":

    - cluster identifies the Kubernetes cluster.

    - action must be one of:

      health,
      nodes,
      pods,
      high_restart_pods,
      pending_pods,
      failed_pods,
      pod_details,
      logs,
      events.

    - namespace should only be extracted when explicitly provided.

    - pod should be extracted when the question identifies
      a specific pod for pod_details or logs.

    - Do not invent generated Kubernetes pod suffixes.

24. Examples of Kubernetes questions:

    "Is Kubernetes cluster Docker Desktop healthy?"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "cluster": "Docker Desktop",
            "action": "health"
        }}
    }}

    "Show Kubernetes nodes"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "action": "nodes"
        }}
    }}

    "Which Kubernetes pods have high restart counts?"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "action": "high_restart_pods"
        }}
    }}

    "Show pending Kubernetes pods"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "action": "pending_pods"
        }}
    }}

    "Show failed pods in namespace default"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "action": "failed_pods",
            "namespace": "default"
        }}
    }}

    "Show logs of validator pod in default namespace"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "action": "logs",
            "namespace": "default",
            "pod": "validator"
        }}
    }}

    "Show Kubernetes events in default namespace"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "action": "events",
            "namespace": "default"
        }}
    }}

Investigation rules:

25. If the engineer asks WHY a Kubernetes pod is failing,
    restarting, crashing, reporting errors, or asks to investigate
    or diagnose a Kubernetes pod problem, select "kubernetes".

26. For Kubernetes investigation questions:

    - identify the pod from the question.

    - identify namespace if explicitly provided.

    - identify cluster if explicitly provided.

    - do not invent a cluster or namespace in the normal
      tool-selection response.

    - investigation-specific local POC defaults are applied
      later by the process() method.

27. Investigation examples:

    "Why is the validator pod failing?"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "pod": "validator"
        }}
    }}

    "Investigate why validator pod is restarting in default"

    ->
    {{
        "tool": "kubernetes",
        "parameters": {{
            "namespace": "default",
            "pod": "validator"
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

    # =============================================================
    # CAPACITY NORMALIZATION
    # =============================================================

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
        # =============================================================
    # INVESTIGATION DETECTION
    # =============================================================

    def _is_investigation_question(
        self,
        question: str,
    ) -> bool:
        """
        Determine whether the engineer is asking for
        multi-signal investigation or diagnosis.

        Investigation questions require multiple live
        signals to be collected and correlated before
        generating the final answer.

        This method only detects the investigation intent.
        """

        if not question or not question.strip():
            return False

        question_lower = (
            question.lower()
        )

        investigation_patterns = [
            r"\bwhy\b.*\b("
            r"fail|failed|failure|"
            r"restart|restarting|"
            r"crash|crashing|"
            r"error|issue|problem"
            r")\b",

            r"\bwhy\s+is\b",
            r"\bwhy\s+are\b",
            r"\binvestigate\b",
            r"\binvestigation\b",
            r"\bdiagnose\b",
            r"\bdiagnosis\b",
            r"\broot\s+cause\b",
            r"\bwhat\s+is\s+causing\b",
            r"\bwhat\s+caused\b",
            r"\bfind\s+the\s+cause\b",
        ]

        return any(
            re.search(
                pattern,
                question_lower,
            )
            for pattern in investigation_patterns
        )

    # =============================================================
    # KUBERNETES MULTI-SIGNAL INVESTIGATION
    # =============================================================

    async def investigate_kubernetes(
        self,
        parameters: dict,
    ) -> dict:
        """
        Perform a read-only multi-signal Kubernetes investigation.

        Signals collected:

        1. Pod details
        2. Pod logs
        3. Kubernetes events
        """

        if not isinstance(
            parameters,
            dict,
        ):
            return {
                "status": "error",
                "error": (
                    "Investigation parameters must "
                    "be a dictionary."
                ),
            }

        cluster = parameters.get(
            "cluster",
            "Docker Desktop",
        )

        namespace = parameters.get(
            "namespace",
            "default",
        )

        pod = parameters.get(
            "pod",
        )

        if not isinstance(
            cluster,
            str,
        ) or not cluster.strip():

            return {
                "status": "error",
                "error": (
                    "Kubernetes cluster is required."
                ),
            }

        if not isinstance(
            namespace,
            str,
        ) or not namespace.strip():

            return {
                "status": "error",
                "error": (
                    "Kubernetes namespace is required."
                ),
            }

        if not isinstance(
            pod,
            str,
        ) or not pod.strip():

            return {
                "status": "error",
                "error": (
                    "A specific Kubernetes pod is required "
                    "for this investigation."
                ),
            }

        base_parameters = {
            "cluster": cluster,
            "namespace": namespace,
            "pod": pod,
        }

        results = {}

        # ---------------------------------------------------------
        # Signal 1: Pod details
        # ---------------------------------------------------------

        results["pod_details"] = (
            await self.execute_tool(
                tool_name="kubernetes",
                parameters={
                    **base_parameters,
                    "action": "pod_details",
                },
            )
        )

        # ---------------------------------------------------------
        # Signal 2: Pod logs
        # ---------------------------------------------------------

        results["logs"] = (
            await self.execute_tool(
                tool_name="kubernetes",
                parameters={
                    **base_parameters,
                    "action": "logs",
                },
            )
        )

        # ---------------------------------------------------------
        # Signal 3: Kubernetes events
        # ---------------------------------------------------------

        results["events"] = (
            await self.execute_tool(
                tool_name="kubernetes",
                parameters={
                    "cluster": cluster,
                    "namespace": namespace,
                    "action": "events",
                },
            )
        )

        successful = all(
            isinstance(
                result,
                dict,
            )
            and result.get("status") == "success"
            for result in results.values()
        )

        return {
            "status": (
                "success"
                if successful
                else "partial"
            ),
            "investigation": (
                "kubernetes_pod_failure"
            ),
            "cluster": cluster,
            "namespace": namespace,
            "pod": pod,
            "signals": results,
        }

    # =============================================================
    # TOOL EXECUTION
    # =============================================================

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

        if not isinstance(
            parameters,
            dict,
        ):
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

            result = await self.tool_executor.execute(
                tool=tool,
                request=request,
                user_context=self.user_context,
            )

            return result

        except PermissionError as exc:

            return {
                "status": "error",
                "error": str(exc),
            }

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

    # =============================================================
    # KNOWLEDGE SEARCH
    # =============================================================

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

    # =============================================================
    # ANSWER GENERATION
    # =============================================================

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

        investigation_rules = ""

        if tool_name == "kubernetes_investigation":
            investigation_rules = """
Investigation rules:

11. For investigation questions, correlate the supplied
    signals before answering.

12. Treat pod details, logs, and Kubernetes events as
    separate evidence sources.

13. Identify findings that are directly supported by
    the supplied evidence.

14. Structure investigation answers using these headings:
    - Root Cause
    - Evidence
    - Impact
    - What Is Not Confirmed

15. Under "Root Cause", state the most specific cause that
    is directly supported by the supplied evidence.

16. Under "Evidence", cite the concrete findings from
    pod details, logs, and events that support the conclusion.

17. Under "Impact", describe only the impact that is directly
    supported by the supplied evidence.

18. Under "What Is Not Confirmed", explicitly identify any
    missing evidence or uncertainty that prevents a stronger
    conclusion.

19. Do not claim a root cause unless the supplied evidence
    directly establishes causation. A symptom, status, event,
    restart count, warning, or correlation is not by itself a
    root cause.

20. Kubernetes "BackOff", "CrashLoopBackOff", restart counts,
    NotReady status, or similar lifecycle signals describe the
    observed failure behavior. They must not be presented as the
    underlying cause unless another supplied evidence source
    explicitly establishes that causation.

21. If the evidence only shows symptoms and does not establish
    the underlying cause, the Root Cause section MUST state:
    "The underlying root cause cannot be confirmed from the
    available evidence."

22. Do not treat a warning as causal merely because it appears
    in the logs. State it as an observation unless the supplied
    evidence explicitly connects the warning to the failure.

23. Do not infer causes such as application defects, resource
    exhaustion, dependency failure, network failure, DNS failure,
    authentication failure, configuration problems, or service
    outages unless the supplied evidence explicitly supports them.

24. Under "Impact", report only directly observed or explicitly
    supported effects. Do not predict possible downtime, degraded
    performance, application impact, or business impact.

25. Do not invent missing logs, events, metrics, conditions,
    causes, impact, or remediation steps.

26. Do not provide remediation commands unless they are present
    in the supplied evidence or relevant internal knowledge.
"""

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

{investigation_rules}

Answer:
"""

        answer = await self.llm.generate(
            prompt
        )

        if tool_name == "kubernetes_investigation":
            format_prompt = f"""
Review and rewrite the investigation answer below into the EXACT
structure required by InfraDB Assist.

Use these headings exactly and in this order:

Root Cause
Evidence
Impact
What Is Not Confirmed

Investigation evidence:
{tool_result}

Draft answer:
{answer}

Strict grounding rules:

1. Use ONLY facts explicitly present in the Investigation evidence.
2. Do not add facts from general model knowledge.
3. Do not infer causation from correlation, status, event type,
   restart count, warning, or lifecycle state.
4. "BackOff", restart counts, NotReady, Waiting, or similar
   Kubernetes signals describe observed failure behavior. They are
   NOT the underlying root cause unless another supplied evidence
   source explicitly establishes causation.
5. If the evidence shows an application exception or explicit
   failure message, report that exact observed failure mechanism.
   Do not claim why the dependency or component is unavailable
   unless the evidence explicitly establishes why.
6. If the underlying root cause is not established, the Root Cause
   section MUST contain exactly this statement:
   "The underlying root cause cannot be confirmed from the available evidence."
7. Under Evidence, list only concrete observations from pod details,
   logs, and events.
8. Under Impact, state only directly observed effects. Do not use
   words such as "could", "may", "might", "likely", or predict
   downtime, degraded performance, application impact, or business impact.
9. Under What Is Not Confirmed, state only uncertainty that follows
   directly from the evidence. Do NOT provide hypothetical causes
   or examples such as network, DNS, authentication, configuration,
   resource, dependency, or service problems unless that exact cause
   is explicitly present in the evidence.
10. Do not say that a warning is harmless or unrelated unless the
    evidence explicitly proves that.
11. Do not invent remediation steps or commands.
12. Keep the answer concise and technical.
13. Return ONLY the four headings and their content.
"""

            answer = await self.llm.generate(
                format_prompt
            )

        return answer
        # =============================================================
    # MAIN ORCHESTRATION
    # =============================================================

    async def process(
        self,
        question: str,
    ) -> dict:
        """
        Complete orchestration flow.

        Normal question:

        Question
            ↓
        Tool Selection
            ↓
        Tool Execution
            ↓
        Knowledge Search
            ↓
        Grounded Answer

        Investigation question:

        Question
            ↓
        Investigation Detection
            ↓
        Tool Selection
            ↓
        Multi-Signal Investigation
            ├── Pod Details
            ├── Logs
            └── Events
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

        is_investigation = (
            self._is_investigation_question(
                question
            )
        )

        # =========================================================
        # MULTI-SIGNAL INVESTIGATION
        # =========================================================

        if (
            is_investigation
            and selected
            and selected.get("tool") == "kubernetes"
        ):

            tool_name = "kubernetes"

            parameters = dict(
                selected.get(
                    "parameters",
                    {},
                )
            )

            # -----------------------------------------------------
            # Local POC defaults apply ONLY to investigations.
            #
            # These defaults are intentionally NOT applied inside
            # select_tool(), because existing normal Kubernetes
            # selection behavior must remain unchanged.
            # -----------------------------------------------------

            if not parameters.get("cluster"):
                parameters["cluster"] = (
                    "Docker Desktop"
                )

            if not parameters.get("namespace"):
                parameters["namespace"] = "default"

            # -----------------------------------------------------
            # Extract pod deterministically if the LLM did not.
            # -----------------------------------------------------

            if not parameters.get("pod"):

                pod_match = re.search(
                    r"\b(?:pod|container)\s+"
                    r"([a-zA-Z0-9._-]+)",
                    question,
                    flags=re.IGNORECASE,
                )

                if pod_match:
                    parameters["pod"] = (
                        pod_match.group(1)
                    )

            tool_result = (
                await self.investigate_kubernetes(
                    parameters
                )
            )

        # =========================================================
        # NORMAL SINGLE-TOOL EXECUTION
        # =========================================================

        elif selected:

            tool_name = selected["tool"]

            parameters = selected["parameters"]

            tool_result = await self.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
            )

        # =========================================================
        # KNOWLEDGE SEARCH
        # =========================================================

        knowledge_results = (
            await self.search_knowledge(
                question=question,
            )
        )

        # =========================================================
        # ANSWER GENERATION
        # =========================================================

        answer_tool_name = (
            "kubernetes_investigation"
            if (
                is_investigation
                and tool_result is not None
            )
            else (
                tool_name
                if tool_name
                else "knowledge_only"
            )
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