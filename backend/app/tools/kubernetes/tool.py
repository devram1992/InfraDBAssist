from kubernetes import client, config
from kubernetes.client.rest import ApiException

from backend.app.tools.base import Tool


class KubernetesTool(Tool):
    """
    Read-only Kubernetes diagnostic tool.

    Supported actions:
        - health
        - nodes
        - pods
        - high_restart_pods
        - pending_pods
        - failed_pods
        - pod_details
        - logs
        - events

    No Kubernetes resources are created, modified, deleted,
    restarted, patched, or executed into.
    """

    name = "kubernetes"

    description = (
        "Read-only Kubernetes cluster diagnostics including "
        "cluster health, nodes, pods, pod details, pod logs, "
        "and Kubernetes events."
    )

    permission = "kubernetes.read"

    read_only = True

    parameters = {
        "cluster": {
            "type": "string",
            "description": "Kubernetes cluster name",
            "required": True,
        },
        "action": {
            "type": "string",
            "description": "Kubernetes inspection action",
            "required": True,
            "allowed": [
                "health",
                "nodes",
                "pods",
                "high_restart_pods",
                "pending_pods",
                "failed_pods",
                "pod_details",
                "logs",
                "events",
            ],
        },
        "namespace": {
            "type": "string",
            "description": "Kubernetes namespace",
            "required": False,
        },
        "pod": {
            "type": "string",
            "description": (
                "Kubernetes pod name or unique pod-name prefix"
            ),
            "required": False,
        },
        "tail_lines": {
            "type": "integer",
            "description": "Number of recent log lines to return",
            "required": False,
        },
    }

    def build_request(self, **kwargs) -> dict:
        """
        Build and validate a Kubernetes diagnostic request.
        """

        cluster = kwargs.get("cluster")

        if not isinstance(cluster, str) or not cluster.strip():
            raise ValueError(
                "Kubernetes cluster must be a non-empty string."
            )

        action = kwargs.get(
            "action",
            "health",
        )

        allowed_actions = {
            "health",
            "nodes",
            "pods",
            "high_restart_pods",
            "pending_pods",
            "failed_pods",
            "pod_details",
            "logs",
            "events",
        }

        if action not in allowed_actions:
            raise ValueError(
                "Unsupported Kubernetes action."
            )

        namespace = kwargs.get("namespace")

        if namespace is not None:
            if not isinstance(namespace, str):
                raise ValueError(
                    "Kubernetes namespace must be a string."
                )

            namespace = namespace.strip()

            if not namespace:
                raise ValueError(
                    "Kubernetes namespace must not be empty."
                )

        pod = kwargs.get("pod")

        if pod is not None:
            if not isinstance(pod, str):
                raise ValueError(
                    "Kubernetes pod must be a string."
                )

            pod = pod.strip()

            if not pod:
                raise ValueError(
                    "Kubernetes pod must not be empty."
                )

        tail_lines = kwargs.get("tail_lines")

        if tail_lines is not None:
            if (
                isinstance(tail_lines, bool)
                or not isinstance(tail_lines, int)
            ):
                raise ValueError(
                    "tail_lines must be a positive integer."
                )

            if tail_lines <= 0:
                raise ValueError(
                    "tail_lines must be a positive integer."
                )

        if action == "pod_details":
            if not namespace:
                raise ValueError(
                    "namespace is required for pod_details."
                )

            if not pod:
                raise ValueError(
                    "pod is required for pod_details."
                )

        if action == "logs":
            if not namespace:
                raise ValueError(
                    "namespace is required for logs."
                )

            if not pod:
                raise ValueError(
                    "pod is required for logs."
                )

        if action == "events":
            if not namespace:
                raise ValueError(
                    "namespace is required for events."
                )

        request = {
            "cluster": cluster,
            "action": action,
            "namespace": namespace,
            "pod": pod,
        }

        if action == "logs":
            request["tail_lines"] = tail_lines

        return request

    async def execute(self, request: dict) -> dict:
        """
        Execute a read-only Kubernetes diagnostic request.
        """

        self.validate_request(request)

        cluster = request.get("cluster")

        action = request.get(
            "action",
            "health",
        )

        namespace = request.get("namespace")

        pod = request.get("pod")

        tail_lines = request.get("tail_lines")

        try:
            config.load_kube_config()

            core_api = client.CoreV1Api()

            # ---------------------------------------------------------
            # POD DETAILS
            # ---------------------------------------------------------

            if action == "pod_details":
                data = await self._get_pod_details(
                    core_api,
                    namespace=namespace,
                    pod=pod,
                )

                return {
                    "tool": self.name,
                    "status": "success",
                    "data": {
                        "cluster": cluster,
                        "action": action,
                        "namespace": namespace,
                        "pod": data,
                    },
                }

            # ---------------------------------------------------------
            # POD LOGS
            # ---------------------------------------------------------

            if action == "logs":
                data = await self._get_pod_logs(
                    core_api,
                    namespace=namespace,
                    pod=pod,
                    tail_lines=tail_lines,
                )

                return {
                    "tool": self.name,
                    "status": "success",
                    "data": {
                        "cluster": cluster,
                        "action": action,
                        "namespace": namespace,
                        "pod": pod,
                        "logs": data,
                    },
                }

            # ---------------------------------------------------------
            # EVENTS
            # ---------------------------------------------------------

            if action == "events":
                data = await self._get_events(
                    core_api,
                    namespace=namespace,
                )

                return {
                    "tool": self.name,
                    "status": "success",
                    "data": {
                        "cluster": cluster,
                        "action": action,
                        "namespace": namespace,
                        "events": data,
                    },
                }

            # ---------------------------------------------------------
            # NODES
            # ---------------------------------------------------------

            nodes_response = core_api.list_node()

            nodes = (
                nodes_response.items
                if nodes_response
                else []
            )

            # ---------------------------------------------------------
            # PODS
            # ---------------------------------------------------------

            if namespace:
                pods_response = (
                    core_api.list_namespaced_pod(
                        namespace=namespace,
                    )
                )
            else:
                pods_response = (
                    core_api.list_pod_for_all_namespaces()
                )

            pods = (
                pods_response.items
                if pods_response
                else []
            )

            node_summary = self._build_node_summary(
                nodes
            )

            pod_summary = self._build_pod_summary(
                pods
            )

            # ---------------------------------------------------------
            # HEALTH
            # ---------------------------------------------------------

            if action == "health":
                data = {
                    "cluster": cluster,
                    "action": action,
                    "nodes": node_summary,
                    "pods": pod_summary,
                }

            # ---------------------------------------------------------
            # NODES
            # ---------------------------------------------------------

            elif action == "nodes":
                data = {
                    "cluster": cluster,
                    "action": action,
                    "nodes": node_summary,
                }

            # ---------------------------------------------------------
            # PODS
            # ---------------------------------------------------------

            elif action == "pods":
                data = {
                    "cluster": cluster,
                    "action": action,
                    "pods": pod_summary,
                }

            # ---------------------------------------------------------
            # HIGH RESTART PODS
            # ---------------------------------------------------------

            elif action == "high_restart_pods":
                data = {
                    "cluster": cluster,
                    "action": action,
                    "pods": pod_summary[
                        "high_restart_pods"
                    ],
                    "count": len(
                        pod_summary[
                            "high_restart_pods"
                        ]
                    ),
                }

            # ---------------------------------------------------------
            # PENDING PODS
            # ---------------------------------------------------------

            elif action == "pending_pods":
                pending = [
                    item
                    for item in pod_summary["items"]
                    if item["phase"] == "Pending"
                ]

                data = {
                    "cluster": cluster,
                    "action": action,
                    "pods": pending,
                    "count": len(pending),
                }

            # ---------------------------------------------------------
            # FAILED PODS
            # ---------------------------------------------------------

            elif action == "failed_pods":
                failed = [
                    item
                    for item in pod_summary["items"]
                    if item["phase"] == "Failed"
                ]

                data = {
                    "cluster": cluster,
                    "action": action,
                    "pods": failed,
                    "count": len(failed),
                }

            else:
                raise ValueError(
                    "Unsupported Kubernetes action."
                )

            return {
                "tool": self.name,
                "status": "success",
                "data": data,
            }

        except Exception as exc:
            return {
                "tool": self.name,
                "status": "error",
                "error": str(exc),
            }

    def _build_node_summary(
        self,
        nodes,
    ) -> dict:
        """
        Build a compact node summary.
        """

        items = []

        ready_count = 0

        for node in nodes:

            name = getattr(
                getattr(node, "metadata", None),
                "name",
                "UNKNOWN",
            )

            conditions = getattr(
                getattr(node, "status", None),
                "conditions",
                None,
            ) or []

            ready = False

            for condition in conditions:

                if (
                    getattr(condition, "type", None)
                    == "Ready"
                ):
                    ready = (
                        getattr(
                            condition,
                            "status",
                            None,
                        )
                        == "True"
                    )

                    break

            if ready:
                ready_count += 1

            node_info = getattr(
                getattr(node, "status", None),
                "node_info",
                None,
            )

            kubelet_version = getattr(
                node_info,
                "kubelet_version",
                None,
            )

            runtime = getattr(
                node_info,
                "container_runtime_version",
                None,
            )

            items.append(
                {
                    "name": name,
                    "status": (
                        "Ready"
                        if ready
                        else "NotReady"
                    ),
                    "kubelet_version": kubelet_version,
                    "runtime": runtime,
                }
            )

        return {
            "count": len(items),
            "ready": ready_count,
            "not_ready": (
                len(items) - ready_count
            ),
            "items": items,
        }

    def _build_pod_summary(
        self,
        pods,
    ) -> dict:
        """
        Build a compact pod summary.
        """

        items = []

        running = 0
        pending = 0
        failed = 0
        succeeded = 0
        restart_total = 0

        for pod in pods:

            metadata = getattr(
                pod,
                "metadata",
                None,
            )

            status = getattr(
                pod,
                "status",
                None,
            )

            name = getattr(
                metadata,
                "name",
                "UNKNOWN",
            )

            pod_namespace = getattr(
                metadata,
                "namespace",
                None,
            )

            phase = getattr(
                status,
                "phase",
                "Unknown",
            )

            container_statuses = getattr(
                status,
                "container_statuses",
                None,
            ) or []

            restart_count = sum(
                getattr(
                    container,
                    "restart_count",
                    0,
                )
                or 0
                for container in container_statuses
            )

            restart_total += restart_count

            if phase == "Running":
                running += 1

            elif phase == "Pending":
                pending += 1

            elif phase == "Failed":
                failed += 1

            elif phase == "Succeeded":
                succeeded += 1

            items.append(
                {
                    "name": name,
                    "namespace": pod_namespace,
                    "phase": phase,
                    "restart_count": restart_count,
                }
            )

        high_restart_pods = sorted(
            items,
            key=lambda item: item[
                "restart_count"
            ],
            reverse=True,
        )

        return {
            "count": len(items),
            "running": running,
            "pending": pending,
            "failed": failed,
            "succeeded": succeeded,
            "restart_total": restart_total,
            "items": items,
            "high_restart_pods": high_restart_pods,
        }

    async def _get_pod_details(
        self,
        core_api,
        namespace: str,
        pod: str,
    ) -> dict:
        """
        Return detailed information about a pod.

        Supports an exact pod name and a unique
        pod-name prefix.
        """

        resolved_pod = pod

        try:

            pod_object = (
                core_api.read_namespaced_pod(
                    name=pod,
                    namespace=namespace,
                )
            )

        except ApiException as exc:

            if exc.status != 404:
                raise

            response = (
                core_api.list_namespaced_pod(
                    namespace=namespace,
                )
            )

            matching_pods = [
                item
                for item in response.items
                if getattr(
                    getattr(
                        item,
                        "metadata",
                        None,
                    ),
                    "name",
                    "",
                ).startswith(pod)
            ]

            if not matching_pods:

                raise ValueError(
                    f"Pod '{pod}' not found in "
                    f"namespace '{namespace}'."
                )

            if len(matching_pods) > 1:

                names = [
                    item.metadata.name
                    for item in matching_pods
                ]

                raise ValueError(
                    f"Pod prefix '{pod}' is ambiguous. "
                    f"Matching pods: "
                    f"{', '.join(names)}"
                )

            resolved_pod = (
                matching_pods[0].metadata.name
            )

            pod_object = (
                core_api.read_namespaced_pod(
                    name=resolved_pod,
                    namespace=namespace,
                )
            )

        metadata = getattr(
            pod_object,
            "metadata",
            None,
        )

        status = getattr(
            pod_object,
            "status",
            None,
        )

        spec = getattr(
            pod_object,
            "spec",
            None,
        )

        container_statuses = getattr(
            status,
            "container_statuses",
            None,
        ) or []

        containers = []

        restart_count = 0

        for container in container_statuses:

            container_restart_count = (
                getattr(
                    container,
                    "restart_count",
                    0,
                )
                or 0
            )

            restart_count += (
                container_restart_count
            )

            state = getattr(
                container,
                "state",
                None,
            )

            running = getattr(
                state,
                "running",
                None,
            )

            waiting = getattr(
                state,
                "waiting",
                None,
            )

            terminated = getattr(
                state,
                "terminated",
                None,
            )

            if running is not None:
                container_state = "running"

            elif waiting is not None:
                container_state = "waiting"

            elif terminated is not None:
                container_state = "terminated"

            else:
                container_state = "unknown"

            containers.append(
                {
                    "name": getattr(
                        container,
                        "name",
                        None,
                    ),
                    "ready": getattr(
                        container,
                        "ready",
                        None,
                    ),
                    "restart_count": (
                        container_restart_count
                    ),
                    "state": container_state,
                    "image": getattr(
                        container,
                        "image",
                        None,
                    ),
                    "image_id": getattr(
                        container,
                        "image_id",
                        None,
                    ),
                }
            )

        conditions = []

        for condition in (
            getattr(
                status,
                "conditions",
                None,
            )
            or []
        ):

            conditions.append(
                {
                    "type": getattr(
                        condition,
                        "type",
                        None,
                    ),
                    "status": getattr(
                        condition,
                        "status",
                        None,
                    ),
                }
            )

        return {
            "name": getattr(
                metadata,
                "name",
                resolved_pod,
            ),
            "namespace": getattr(
                metadata,
                "namespace",
                namespace,
            ),
            "uid": getattr(
                metadata,
                "uid",
                None,
            ),
            "labels": getattr(
                metadata,
                "labels",
                None,
            ),
            "phase": getattr(
                status,
                "phase",
                "Unknown",
            ),
            "pod_ip": getattr(
                status,
                "pod_ip",
                None,
            ),
            "host_ip": getattr(
                status,
                "host_ip",
                None,
            ),
            "node_name": getattr(
                spec,
                "node_name",
                None,
            ),
            "conditions": conditions,
            "restart_count": restart_count,
            "containers": containers,
        }

    async def _get_pod_logs(
        self,
        core_api,
        namespace: str,
        pod: str,
        tail_lines=None,
    ) -> dict:
        """
        Read pod logs without modifying the pod.

        Supports either the exact pod name or a unique
        pod-name prefix.
        """

        resolved_pod = pod

        try:

            core_api.read_namespaced_pod(
                name=pod,
                namespace=namespace,
            )

        except ApiException as exc:

            if exc.status != 404:
                raise

            response = (
                core_api.list_namespaced_pod(
                    namespace=namespace,
                )
            )

            matching_pods = [
                item
                for item in response.items
                if getattr(
                    getattr(
                        item,
                        "metadata",
                        None,
                    ),
                    "name",
                    "",
                ).startswith(pod)
            ]

            if not matching_pods:

                raise ValueError(
                    f"Pod '{pod}' not found in "
                    f"namespace '{namespace}'."
                )

            if len(matching_pods) > 1:

                names = [
                    item.metadata.name
                    for item in matching_pods
                ]

                raise ValueError(
                    f"Pod prefix '{pod}' is ambiguous. "
                    f"Matching pods: "
                    f"{', '.join(names)}"
                )

            resolved_pod = (
                matching_pods[0].metadata.name
            )

        kwargs = {
            "name": resolved_pod,
            "namespace": namespace,
        }

        if tail_lines is not None:
            kwargs["tail_lines"] = tail_lines

        logs = (
            core_api.read_namespaced_pod_log(
                **kwargs
            )
        )

        return {
            "pod": resolved_pod,
            "namespace": namespace,
            "tail_lines": tail_lines,
            "content": logs,
        }

    async def _get_events(
        self,
        core_api,
        namespace: str,
    ) -> dict:
        """
        Return compact Kubernetes events for a namespace.
        """

        response = (
            core_api.list_namespaced_event(
                namespace=namespace,
            )
        )

        events = []

        for event in (
            getattr(
                response,
                "items",
                None,
            )
            or []
        ):

            metadata = getattr(
                event,
                "metadata",
                None,
            )

            involved_object = getattr(
                event,
                "involved_object",
                None,
            )

            events.append(
                {
                    "type": getattr(
                        event,
                        "type",
                        None,
                    ),
                    "reason": getattr(
                        event,
                        "reason",
                        None,
                    ),
                    "message": getattr(
                        event,
                        "message",
                        None,
                    ),
                    "count": getattr(
                        event,
                        "count",
                        None,
                    ),
                    "namespace": getattr(
                        metadata,
                        "namespace",
                        namespace,
                    ),
                    "object": getattr(
                        involved_object,
                        "name",
                        None,
                    ),
                    "object_kind": getattr(
                        involved_object,
                        "kind",
                        None,
                    ),
                }
            )

        return {
            "count": len(events),
            "items": events,
        }