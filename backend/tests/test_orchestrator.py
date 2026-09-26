import pytest

from backend.app.ai.orchestrator import AIOrchestrator


@pytest.mark.asyncio
async def test_process_supports_knowledge_only_question(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question):
        return None

    async def mock_search_knowledge(
        question,
        limit=5,
    ):
        return [
            {
                "title": "database_backup",
                "source_type": "sop",
                "similarity": 0.85,
                "content": (
                    "Verify backup completion "
                    "and archive logs."
                ),
            }
        ]

    async def mock_generate_answer(
        question,
        tool_name,
        tool_result,
        knowledge_results,
    ):
        assert tool_name == "knowledge_only"
        assert tool_result == {}
        assert len(knowledge_results) == 1

        return (
            "Use the database backup SOP "
            "to verify completion."
        )

    monkeypatch.setattr(
        orchestrator,
        "select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "search_knowledge",
        mock_search_knowledge,
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        mock_generate_answer,
    )

    result = await orchestrator.process(
        "How do I verify database backups?"
    )

    assert result["status"] == "success"
    assert result["selected_tool"] is None
    assert result["parameters"] == {}
    assert result["tool_result"] is None
    assert len(result["knowledge_results"]) == 1
    assert (
        result["answer"]
        == "Use the database backup SOP to verify completion."
    )


@pytest.mark.asyncio
async def test_process_executes_selected_tool_and_searches_knowledge(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "PRODDB",
            },
        }

    async def mock_execute_tool(
        tool_name,
        parameters=None,
    ):
        assert tool_name == "oracle_database"
        assert parameters == {
            "database": "PRODDB",
        }

        return {
            "status": "success",
            "database": "PRODDB",
            "state": "OPEN",
        }

    async def mock_search_knowledge(
        question,
        limit=5,
    ):
        return [
            {
                "title": "oracle_performance",
                "source_type": "runbook",
                "similarity": 0.90,
                "content": (
                    "Review active sessions "
                    "and wait events."
                ),
            }
        ]

    async def mock_generate_answer(
        question,
        tool_name,
        tool_result,
        knowledge_results,
    ):
        assert tool_name == "oracle_database"
        assert tool_result["database"] == "PRODDB"
        assert len(knowledge_results) == 1

        return "PRODDB is OPEN."

    monkeypatch.setattr(
        orchestrator,
        "select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "execute_tool",
        mock_execute_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "search_knowledge",
        mock_search_knowledge,
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        mock_generate_answer,
    )

    result = await orchestrator.process(
        "Check Oracle database PRODDB performance"
    )

    assert result["status"] == "success"
    assert (
        result["selected_tool"]
        == "oracle_database"
    )
    assert result["parameters"] == {
        "database": "PRODDB",
    }
    assert (
        result["tool_result"]["database"]
        == "PRODDB"
    )
    assert len(
        result["knowledge_results"]
    ) == 1
    assert (
        result["answer"]
        == "PRODDB is OPEN."
    )


@pytest.mark.asyncio
async def test_select_tool_accepts_valid_tool_and_parameters(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "PRODDB",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Check Oracle database PRODDB."
    )

    assert result == {
        "tool": "oracle_database",
        "parameters": {
            "database": "PRODDB",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_returns_none_for_knowledge_only_question(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "NONE",
            "parameters": {},
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "What is Oracle RAC?"
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_returns_none_for_procedure_question(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "NONE",
            "parameters": {},
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "How do I perform an Oracle database backup?"
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_returns_none_for_explanation_question(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "NONE",
            "parameters": {},
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Explain Oracle Data Guard."
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_returns_none_for_troubleshooting_question(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "NONE",
            "parameters": {},
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "How can I troubleshoot Oracle blocking sessions?"
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_rejects_unknown_tool(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "unknown_tool",
            "parameters": {},
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Check database status."
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_rejects_invalid_parameters(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "PRODDB",
                "invalid_parameter": "value",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Check Oracle database PRODDB."
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_handles_invalid_json(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        raise ValueError(
            "LLM returned invalid JSON"
        )

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Check Oracle database PRODDB."
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_rejects_non_dict_response(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return [
            "oracle_database",
            {
                "database": "PRODDB",
            },
        ]

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Check Oracle database PRODDB."
    )

    assert result is None


@pytest.mark.asyncio
async def test_select_tool_accepts_oracle_sessions_action(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "FREEPDB1",
                "action": "sessions",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Show active Oracle sessions in FREEPDB1."
    )

    assert result == {
        "tool": "oracle_database",
        "parameters": {
            "database": "FREEPDB1",
            "action": "sessions",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_oracle_tablespace_action(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "FREEPDB1",
                "action": "tablespace",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Show Oracle tablespace usage for FREEPDB1."
    )

    assert result == {
        "tool": "oracle_database",
        "parameters": {
            "database": "FREEPDB1",
            "action": "tablespace",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_oracle_blocking_sessions_action(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "FREEPDB1",
                "action": "blocking_sessions",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Show the blocking sessions in FREEPDB1."
    )

    assert result == {
        "tool": "oracle_database",
        "parameters": {
            "database": "FREEPDB1",
            "action": "blocking_sessions",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_oracle_long_running_sessions_action(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "FREEPDB1",
                "action": "long_running_sessions",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Show long-running Oracle sessions in FREEPDB1."
    )

    assert result == {
        "tool": "oracle_database",
        "parameters": {
            "database": "FREEPDB1",
            "action": "long_running_sessions",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_capacity_forecast(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "capacity_forecast",
            "parameters": {
                "target": "FREEPDB1",
                "resource": "SYSTEM",
                "threshold": 99,
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "When will SYSTEM tablespace in FREEPDB1 reach 99%?"
    )

    assert result == {
        "tool": "capacity_forecast",
        "parameters": {
            "target": "FREEPDB1",
            "resource": "SYSTEM",
            "metric": "used_percent",
            "unit": "percent",
            "threshold": 99,
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_capacity_forecast_with_horizon(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "capacity_forecast",
            "parameters": {
                "target": "FREEPDB1",
                "resource": "SYSTEM",
                "horizon_days": 30,
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Forecast SYSTEM tablespace usage in FREEPDB1 "
        "for the next 30 days."
    )

    assert result == {
        "tool": "capacity_forecast",
        "parameters": {
            "target": "FREEPDB1",
            "resource": "SYSTEM",
            "metric": "used_mb",
            "unit": "MB",
            "horizon_days": 30,
        },
    }


@pytest.mark.asyncio
async def test_capacity_forecast_tool_is_registered():
    orchestrator = AIOrchestrator()

    assert orchestrator.tool_registry.has(
        "capacity_forecast"
    )


@pytest.mark.asyncio
async def test_process_executes_capacity_forecast(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question):
        return {
            "tool": "capacity_forecast",
            "parameters": {
                "target": "FREEPDB1",
                "resource": "SYSTEM",
                "threshold": 99,
            },
        }

    async def mock_execute_tool(
        tool_name,
        parameters=None,
    ):
        assert tool_name == "capacity_forecast"
        assert parameters == {
            "target": "FREEPDB1",
            "resource": "SYSTEM",
            "threshold": 99,
        }

        return {
            "tool": "capacity_forecast",
            "status": "success",
            "target": "FREEPDB1",
            "resource": "SYSTEM",
            "forecast": {
                "current_value": 98.52,
                "trend": "increasing",
                "growth_per_day": 0.4,
                "horizon_days": 30,
                "projected_value": 110.52,
                "threshold": {
                    "configured": True,
                    "threshold": 99.0,
                    "status": "breach_predicted",
                    "days_until_breach": 1.2,
                },
            },
        }

    async def mock_search_knowledge(
        question,
        limit=5,
    ):
        return []

    async def mock_generate_answer(
        question,
        tool_name,
        tool_result,
        knowledge_results,
    ):
        assert tool_name == "capacity_forecast"
        assert tool_result["resource"] == "SYSTEM"
        assert (
            tool_result["forecast"]["current_value"]
            == 98.52
        )

        return (
            "SYSTEM is currently at 98.52% "
            "and the forecast predicts a threshold breach."
        )

    monkeypatch.setattr(
        orchestrator,
        "select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "execute_tool",
        mock_execute_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "search_knowledge",
        mock_search_knowledge,
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        mock_generate_answer,
    )

    result = await orchestrator.process(
        "When will SYSTEM tablespace in FREEPDB1 reach 99%?"
    )

    assert result["status"] == "success"
    assert (
        result["selected_tool"]
        == "capacity_forecast"
    )
    assert result["parameters"] == {
        "target": "FREEPDB1",
        "resource": "SYSTEM",
        "threshold": 99,
    }
    assert (
        result["tool_result"]["resource"]
        == "SYSTEM"
    )


@pytest.mark.asyncio
async def test_select_tool_accepts_kubernetes_health_action(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "kubernetes",
            "parameters": {
                "cluster": "Docker Desktop",
                "action": "health",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Is the Docker Desktop Kubernetes cluster healthy?"
    )

    assert result == {
        "tool": "kubernetes",
        "parameters": {
            "cluster": "Docker Desktop",
            "action": "health",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_kubernetes_high_restart_action(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "kubernetes",
            "parameters": {
                "action": "high_restart_pods",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Which Kubernetes pods have high restart counts?"
    )

    assert result == {
        "tool": "kubernetes",
        "parameters": {
            "action": "high_restart_pods",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_kubernetes_pending_action(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "kubernetes",
            "parameters": {
                "action": "pending_pods",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Show pending Kubernetes pods."
    )

    assert result == {
        "tool": "kubernetes",
        "parameters": {
            "action": "pending_pods",
        },
    }


@pytest.mark.asyncio
async def test_select_tool_accepts_kubernetes_failed_action_with_namespace(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_generate_json(prompt):
        return {
            "tool": "kubernetes",
            "parameters": {
                "action": "failed_pods",
                "namespace": "default",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Show failed pods in namespace default."
    )

    assert result == {
        "tool": "kubernetes",
        "parameters": {
            "action": "failed_pods",
            "namespace": "default",
        },
    }


@pytest.mark.asyncio
async def test_investigate_kubernetes_collects_all_signals(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    calls = []

    async def mock_execute_tool(
        tool_name,
        parameters=None,
    ):
        calls.append(
            (
                tool_name,
                parameters,
            )
        )

        action = parameters["action"]

        if action == "pod_details":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "pod": "validator-abc123",
                    "namespace": "default",
                    "status": "CrashLoopBackOff",
                },
            }

        if action == "logs":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "pod": "validator-abc123",
                    "namespace": "default",
                    "logs": {
                        "content": "Kafka not available after retries"
                    },
                },
            }

        if action == "events":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "namespace": "default",
                    "events": {
                        "count": 1,
                        "items": [
                            {
                                "type": "Warning",
                                "reason": "BackOff",
                                "message": (
                                    "Back-off restarting failed "
                                    "container validator"
                                ),
                            }
                        ],
                    },
                },
            }

        raise AssertionError(
            f"Unexpected action: {action}"
        )

    monkeypatch.setattr(
        orchestrator,
        "execute_tool",
        mock_execute_tool,
    )

    result = await orchestrator.investigate_kubernetes(
        {
            "cluster": "Docker Desktop",
            "namespace": "default",
            "pod": "validator",
        }
    )

    assert result["status"] == "success"
    assert result["investigation"] == "kubernetes_pod_failure"
    assert result["cluster"] == "Docker Desktop"
    assert result["namespace"] == "default"
    assert result["pod"] == "validator"

    assert set(result["signals"]) == {
        "pod_details",
        "logs",
        "events",
    }

    assert calls == [
        (
            "kubernetes",
            {
                "cluster": "Docker Desktop",
                "action": "pod_details",
                "namespace": "default",
                "pod": "validator",
            },
        ),
        (
            "kubernetes",
            {
                "cluster": "Docker Desktop",
                "action": "logs",
                "namespace": "default",
                "pod": "validator",
            },
        ),
        (
            "kubernetes",
            {
                "cluster": "Docker Desktop",
                "action": "events",
                "namespace": "default",
            },
        ),
    ]


@pytest.mark.asyncio
async def test_investigate_kubernetes_returns_partial_when_signal_fails(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_execute_tool(
        tool_name,
        parameters=None,
    ):
        action = parameters["action"]

        if action == "pod_details":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "pod": "validator-abc123",
                    "namespace": "default",
                    "status": "CrashLoopBackOff",
                },
            }

        if action == "logs":
            return {
                "tool": "kubernetes",
                "status": "error",
                "error": "Unable to read pod logs.",
            }

        if action == "events":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "namespace": "default",
                    "events": {
                        "count": 1,
                        "items": [
                            {
                                "type": "Warning",
                                "reason": "BackOff",
                                "message": (
                                    "Back-off restarting failed "
                                    "container validator"
                                ),
                            }
                        ],
                    },
                },
            }

        raise AssertionError(
            f"Unexpected action: {action}"
        )

    monkeypatch.setattr(
        orchestrator,
        "execute_tool",
        mock_execute_tool,
    )

    result = await orchestrator.investigate_kubernetes(
        {
            "cluster": "Docker Desktop",
            "namespace": "default",
            "pod": "validator",
        }
    )

    assert result["status"] == "partial"
    assert result["investigation"] == "kubernetes_pod_failure"
    assert len(result["signals"]) == 3
    assert (
        result["signals"]["logs"]["status"]
        == "error"
    )


@pytest.mark.asyncio
async def test_process_investigation_applies_local_kubernetes_defaults(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question):
        return {
            "tool": "kubernetes",
            "parameters": {
                "pod": "validator",
            },
        }

    async def mock_investigate_kubernetes(parameters):
        assert parameters == {
            "pod": "validator",
            "cluster": "Docker Desktop",
            "namespace": "default",
        }

        return {
            "status": "success",
            "investigation": "kubernetes_pod_failure",
            "cluster": "Docker Desktop",
            "namespace": "default",
            "pod": "validator",
            "signals": {
                "pod_details": {
                    "status": "success",
                },
                "logs": {
                    "status": "success",
                },
                "events": {
                    "status": "success",
                },
            },
        }

    async def mock_search_knowledge(
        question,
        limit=5,
    ):
        return []

    async def mock_generate_answer(
        question,
        tool_name,
        tool_result,
        knowledge_results,
    ):
        assert tool_name == "kubernetes_investigation"
        assert tool_result["investigation"] == (
            "kubernetes_pod_failure"
        )
        return "Investigation completed."

    monkeypatch.setattr(
        orchestrator,
        "select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "investigate_kubernetes",
        mock_investigate_kubernetes,
    )

    monkeypatch.setattr(
        orchestrator,
        "search_knowledge",
        mock_search_knowledge,
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        mock_generate_answer,
    )

    result = await orchestrator.process(
        "Why is the validator pod failing?"
    )

    assert result["status"] == "success"
    assert result["selected_tool"] == "kubernetes"
    assert result["parameters"] == {
        "pod": "validator",
        "cluster": "Docker Desktop",
        "namespace": "default",
    }
    assert result["tool_result"]["investigation"] == (
        "kubernetes_pod_failure"
    )
    assert result["answer"] == (
        "Investigation completed."
    )


@pytest.mark.asyncio
async def test_process_keeps_normal_kubernetes_question_as_single_tool_execution(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question):
        return {
            "tool": "kubernetes",
            "parameters": {
                "action": "pods",
            },
        }

    async def mock_execute_tool(
        tool_name,
        parameters=None,
    ):
        assert tool_name == "kubernetes"
        assert parameters == {
            "action": "pods",
        }

        return {
            "tool": "kubernetes",
            "status": "success",
            "data": {
                "pods": [],
            },
        }

    async def mock_search_knowledge(
        question,
        limit=5,
    ):
        return []

    async def mock_generate_answer(
        question,
        tool_name,
        tool_result,
        knowledge_results,
    ):
        assert tool_name == "kubernetes"
        assert tool_result["status"] == "success"
        return "No Kubernetes pods found."

    monkeypatch.setattr(
        orchestrator,
        "select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "execute_tool",
        mock_execute_tool,
    )

    monkeypatch.setattr(
        orchestrator,
        "search_knowledge",
        mock_search_knowledge,
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        mock_generate_answer,
    )

    result = await orchestrator.process(
        "Show Kubernetes pods."
    )

    assert result["status"] == "success"
    assert result["selected_tool"] == "kubernetes"
    assert result["parameters"] == {
        "action": "pods",
    }
    assert result["tool_result"]["status"] == "success"
    assert result["answer"] == (
        "No Kubernetes pods found."
    )