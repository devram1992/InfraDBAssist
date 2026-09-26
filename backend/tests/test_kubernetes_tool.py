from types import SimpleNamespace

from unittest.mock import Mock

import pytest

from backend.app.tools.kubernetes.tool import KubernetesTool


def make_node(
    name,
    ready=True,
    kubelet_version="v1.34.1",
    runtime="docker://28.5.1",
):
    conditions = [
        SimpleNamespace(
            type="Ready",
            status="True" if ready else "False",
        ),
        SimpleNamespace(
            type="MemoryPressure",
            status="False",
        ),
    ]

    return SimpleNamespace(
        metadata=SimpleNamespace(
            name=name,
        ),
        status=SimpleNamespace(
            conditions=conditions,
            node_info=SimpleNamespace(
                kubelet_version=kubelet_version,
                container_runtime_version=runtime,
            ),
        ),
    )


def make_pod(
    name,
    namespace="default",
    phase="Running",
    restart_count=0,
):
    return SimpleNamespace(
        metadata=SimpleNamespace(
            name=name,
            namespace=namespace,
        ),
        status=SimpleNamespace(
            phase=phase,
            container_statuses=[
                SimpleNamespace(
                    restart_count=restart_count,
                )
            ],
        ),
    )


@pytest.mark.asyncio
async def test_build_request_defaults_to_health():
    tool = KubernetesTool()

    request = tool.build_request(
        cluster="Docker Desktop",
    )

    assert request == {
        "cluster": "Docker Desktop",
        "action": "health",
        "namespace": None,
        "pod": None,
    }


@pytest.mark.asyncio
async def test_build_request_accepts_action_and_namespace():
    tool = KubernetesTool()

    request = tool.build_request(
        cluster="Docker Desktop",
        action="pods",
        namespace="monitoring",
    )

    assert request == {
        "cluster": "Docker Desktop",
        "action": "pods",
        "namespace": "monitoring",
        "pod": None,
    }


def test_build_request_rejects_empty_cluster():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(cluster="")


def test_build_request_rejects_invalid_action():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(
            cluster="Docker Desktop",
            action="delete",
        )


def test_build_request_rejects_non_string_namespace():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(
            cluster="Docker Desktop",
            namespace=123,
        )


def test_build_node_summary():
    tool = KubernetesTool()

    nodes = [
        make_node("docker-desktop", ready=True),
        make_node("worker-01", ready=False),
    ]

    result = tool._build_node_summary(nodes)

    assert result["count"] == 2
    assert result["ready"] == 1
    assert result["not_ready"] == 1

    assert result["items"][0]["name"] == "docker-desktop"
    assert result["items"][0]["status"] == "Ready"

    assert result["items"][1]["name"] == "worker-01"
    assert result["items"][1]["status"] == "NotReady"


def test_build_pod_summary():
    tool = KubernetesTool()

    pods = [
        make_pod(
            "app-1",
            phase="Running",
            restart_count=2,
        ),
        make_pod(
            "app-2",
            phase="Pending",
            restart_count=0,
        ),
        make_pod(
            "app-3",
            phase="Failed",
            restart_count=5,
        ),
        make_pod(
            "app-4",
            phase="Succeeded",
            restart_count=0,
        ),
    ]

    result = tool._build_pod_summary(pods)

    assert result["count"] == 4
    assert result["running"] == 1
    assert result["pending"] == 1
    assert result["failed"] == 1
    assert result["succeeded"] == 1
    assert result["restart_total"] == 7

    assert len(result["high_restart_pods"]) == 4

    assert (
        result["high_restart_pods"][0]["name"]
        == "app-3"
    )

    assert (
        result["high_restart_pods"][0]["restart_count"]
        == 5
    )

    assert (
        result["high_restart_pods"][1]["name"]
        == "app-1"
    )

    assert (
        result["high_restart_pods"][1]["restart_count"]
        == 2
    )


@pytest.mark.asyncio
async def test_execute_returns_cluster_health(
    monkeypatch,
):
    tool = KubernetesTool()

    mock_nodes = [
        make_node("docker-desktop"),
    ]

    mock_pods = [
        make_pod(
            "validator",
            namespace="default",
            phase="Running",
            restart_count=3154,
        ),
        make_pod(
            "my-app",
            namespace="default",
            phase="Running",
            restart_count=4,
        ),
    ]

    mock_core_api = Mock()

    mock_core_api.list_node.return_value = (
        SimpleNamespace(items=mock_nodes)
    )

    mock_core_api.list_pod_for_all_namespaces.return_value = (
        SimpleNamespace(items=mock_pods)
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.config.load_kube_config",
        Mock(),
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.client.CoreV1Api",
        Mock(return_value=mock_core_api),
    )

    result = await tool.execute(
        {
            "cluster": "Docker Desktop",
            "action": "health",
            "namespace": None,
        }
    )

    assert result["status"] == "success"

    assert (
        result["data"]["cluster"]
        == "Docker Desktop"
    )

    assert result["data"]["nodes"]["count"] == 1
    assert result["data"]["nodes"]["ready"] == 1

    assert result["data"]["pods"]["count"] == 2
    assert result["data"]["pods"]["running"] == 2

    assert (
        result["data"]["pods"]["high_restart_pods"][0]["name"]
        == "validator"
    )

    assert (
        result["data"]["pods"]["high_restart_pods"][0][
            "restart_count"
        ]
        == 3154
    )


@pytest.mark.asyncio
async def test_execute_uses_namespace_filter(
    monkeypatch,
):
    tool = KubernetesTool()

    mock_nodes = [
        make_node("docker-desktop"),
    ]

    mock_pods = [
        make_pod(
            "grafana",
            namespace="monitoring",
            phase="Running",
            restart_count=9,
        ),
    ]

    mock_core_api = Mock()

    mock_core_api.list_node.return_value = (
        SimpleNamespace(items=mock_nodes)
    )

    mock_core_api.list_namespaced_pod.return_value = (
        SimpleNamespace(items=mock_pods)
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.config.load_kube_config",
        Mock(),
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.client.CoreV1Api",
        Mock(return_value=mock_core_api),
    )

    result = await tool.execute(
        {
            "cluster": "Docker Desktop",
            "action": "pods",
            "namespace": "monitoring",
        }
    )

    assert result["status"] == "success"

    mock_core_api.list_namespaced_pod.assert_called_once_with(
        namespace="monitoring",
    )

    assert (
        result["data"]["pods"]["count"]
        == 1
    )


@pytest.mark.asyncio
async def test_execute_returns_error_when_kubernetes_fails(
    monkeypatch,
):
    tool = KubernetesTool()

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.config.load_kube_config",
        Mock(
            side_effect=RuntimeError(
                "Unable to load Kubernetes configuration"
            )
        ),
    )

    result = await tool.execute(
        {
            "cluster": "Docker Desktop",
            "action": "health",
            "namespace": None,
        }
    )

    assert result["status"] == "error"

    assert (
        "Unable to load Kubernetes configuration"
        in result["error"]
    )


@pytest.mark.asyncio
async def test_execute_handles_empty_cluster_data(
    monkeypatch,
):
    tool = KubernetesTool()

    mock_core_api = Mock()

    mock_core_api.list_node.return_value = (
        SimpleNamespace(items=[])
    )

    mock_core_api.list_pod_for_all_namespaces.return_value = (
        SimpleNamespace(items=[])
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.config.load_kube_config",
        Mock(),
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.client.CoreV1Api",
        Mock(return_value=mock_core_api),
    )

    result = await tool.execute(
        {
            "cluster": "Docker Desktop",
            "action": "health",
            "namespace": None,
        }
    )

    assert result["status"] == "success"

    assert result["data"]["nodes"]["count"] == 0
    assert result["data"]["nodes"]["ready"] == 0

    assert result["data"]["pods"]["count"] == 0
    assert result["data"]["pods"]["running"] == 0
    assert result["data"]["pods"]["pending"] == 0
    assert result["data"]["pods"]["failed"] == 0


def test_build_request_requires_pod_for_pod_details():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(
            cluster="Docker Desktop",
            action="pod_details",
            namespace="default",
        )


def test_build_request_requires_namespace_for_pod_details():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(
            cluster="Docker Desktop",
            action="pod_details",
            pod="validator",
        )


@pytest.mark.asyncio
async def test_get_pod_details():
    tool = KubernetesTool()

    container_status = SimpleNamespace(
        name="validator",
        ready=True,
        restart_count=3164,
        state=SimpleNamespace(
            running=SimpleNamespace(),
            waiting=None,
            terminated=None,
        ),
        image="validator:latest",
        image_id="docker://sha256:test",
    )

    mock_pod = SimpleNamespace(
        metadata=SimpleNamespace(
            namespace="default",
            name="validator-59d58784f-bj6ss",
            uid="test-uid",
            labels={
                "app": "validator",
            },
        ),
        status=SimpleNamespace(
            phase="Running",
            pod_ip="10.1.0.152",
            host_ip="192.168.65.3",
            conditions=[
                SimpleNamespace(
                    type="Ready",
                    status="True",
                ),
            ],
            container_statuses=[
                container_status,
            ],
        ),
        spec=SimpleNamespace(
            node_name="docker-desktop",
        ),
    )

    mock_core_api = Mock()

    mock_core_api.read_namespaced_pod.return_value = (
        mock_pod
    )

    result = await tool._get_pod_details(
        mock_core_api,
        namespace="default",
        pod="validator-59d58784f-bj6ss",
    )

    assert (
        result["name"]
        == "validator-59d58784f-bj6ss"
    )

    assert result["namespace"] == "default"
    assert result["phase"] == "Running"
    assert result["node_name"] == "docker-desktop"
    assert result["restart_count"] == 3164

    assert (
        result["containers"][0]["name"]
        == "validator"
    )

    assert (
        result["containers"][0]["restart_count"]
        == 3164
    )

    mock_core_api.read_namespaced_pod.assert_called_once_with(
        name="validator-59d58784f-bj6ss",
        namespace="default",
    )


# ---------------------------------------------------------------------------
# Kubernetes pod logs tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_request_accepts_logs():
    tool = KubernetesTool()

    request = tool.build_request(
        cluster="Docker Desktop",
        action="logs",
        namespace="default",
        pod="validator",
        tail_lines=100,
    )

    assert request == {
        "cluster": "Docker Desktop",
        "action": "logs",
        "namespace": "default",
        "pod": "validator",
        "tail_lines": 100,
    }


def test_build_request_logs_requires_pod():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(
            cluster="Docker Desktop",
            action="logs",
            namespace="default",
        )


def test_build_request_logs_requires_namespace():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(
            cluster="Docker Desktop",
            action="logs",
            pod="validator",
        )


@pytest.mark.asyncio
async def test_execute_returns_pod_logs(monkeypatch):
    tool = KubernetesTool()

    mock_core_api = Mock()

    mock_core_api.read_namespaced_pod_log.return_value = (
        "line 1\nline 2\nline 3"
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.config.load_kube_config",
        Mock(),
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.client.CoreV1Api",
        Mock(return_value=mock_core_api),
    )

    result = await tool.execute(
        {
            "cluster": "Docker Desktop",
            "action": "logs",
            "namespace": "default",
            "pod": "validator",
            "tail_lines": 100,
        }
    )

    assert result["status"] == "success"

    assert (
        result["data"]["cluster"]
        == "Docker Desktop"
    )

    assert (
        result["data"]["namespace"]
        == "default"
    )

    assert (
        result["data"]["pod"]
        == "validator"
    )

    assert (
        result["data"]["logs"]["content"]
        == "line 1\nline 2\nline 3"
    )

    mock_core_api.read_namespaced_pod_log.assert_called_once_with(
        name="validator",
        namespace="default",
        tail_lines=100,
    )
def test_build_request_events_requires_namespace():
    tool = KubernetesTool()

    with pytest.raises(ValueError):
        tool.build_request(
            cluster="Docker Desktop",
            action="events",
        )


@pytest.mark.asyncio
async def test_execute_returns_kubernetes_events(monkeypatch):
    tool = KubernetesTool()

    mock_event = SimpleNamespace(
        type="Warning",
        reason="BackOff",
        message="Back-off restarting failed container",
        count=5,
        metadata=SimpleNamespace(
            namespace="default",
        ),
        involved_object=SimpleNamespace(
            name="validator",
            kind="Pod",
        ),
    )

    mock_core_api = Mock()

    mock_core_api.list_namespaced_event.return_value = (
        SimpleNamespace(
            items=[mock_event],
        )
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.config.load_kube_config",
        Mock(),
    )

    monkeypatch.setattr(
        "backend.app.tools.kubernetes.tool.client.CoreV1Api",
        Mock(return_value=mock_core_api),
    )

    result = await tool.execute(
        {
            "cluster": "Docker Desktop",
            "action": "events",
            "namespace": "default",
            "pod": None,
        }
    )

    assert result["status"] == "success"

    assert (
        result["data"]["cluster"]
        == "Docker Desktop"
    )

    assert (
        result["data"]["namespace"]
        == "default"
    )

    assert (
        result["data"]["events"]["count"]
        == 1
    )

    event = result["data"]["events"]["items"][0]

    assert event["type"] == "Warning"
    assert event["reason"] == "BackOff"
    assert (
        event["object"]
        == "validator"
    )
    assert (
        event["object_kind"]
        == "Pod"
    )

    mock_core_api.list_namespaced_event.assert_called_once_with(
        namespace="default",
    )