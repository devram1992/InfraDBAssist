import pytest

from backend.app.ai.orchestrator import AIOrchestrator
from backend.app.auth.user_context import UserContext


TEST_USER_CONTEXT = UserContext(
    user_id="test-user",
    username="platform-engineer",
    roles={"platform_engineer"},
    permissions={
        "database.read",
        "infrastructure.read",
        "kubernetes.read",
        "capacity.read",
    },
)


@pytest.mark.asyncio
async def test_process_supports_knowledge_only_question(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question, user_context=None):
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
        "How do I verify database backups?",
        user_context=TEST_USER_CONTEXT,
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

    async def mock_select_tool(question, user_context=None):
        return {
            "tool": "oracle_database",
            "parameters": {
                "database": "PRODDB",
            },
        }

    async def mock_execute_tool(
        tool_name,
        parameters=None,
        user_context=None,
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
        "Check Oracle database PRODDB performance",
        user_context=TEST_USER_CONTEXT,
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
        "Check Oracle database PRODDB.",
        user_context=TEST_USER_CONTEXT,
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
        "What is Oracle RAC?",
        user_context=TEST_USER_CONTEXT,
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
        "How do I perform an Oracle database backup?",
        user_context=TEST_USER_CONTEXT,
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
        "Explain Oracle Data Guard.",
        user_context=TEST_USER_CONTEXT,
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
        "How can I troubleshoot Oracle blocking sessions?",
        user_context=TEST_USER_CONTEXT,
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
        "Check database status.",
        user_context=TEST_USER_CONTEXT,
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
        "Check Oracle database PRODDB.",
        user_context=TEST_USER_CONTEXT,
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
        "Check Oracle database PRODDB.",
        user_context=TEST_USER_CONTEXT,
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
        "Check Oracle database PRODDB.",
        user_context=TEST_USER_CONTEXT,
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
        "Show active Oracle sessions in FREEPDB1.",
        user_context=TEST_USER_CONTEXT,
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
        "Show Oracle tablespace usage for FREEPDB1.",
        user_context=TEST_USER_CONTEXT,
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
        "Show the blocking sessions in FREEPDB1.",
        user_context=TEST_USER_CONTEXT,
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
        "Show long-running Oracle sessions in FREEPDB1.",
        user_context=TEST_USER_CONTEXT,
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
        "When will SYSTEM tablespace in FREEPDB1 reach 99%?",
        user_context=TEST_USER_CONTEXT,
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
        "for the next 30 days.",
        user_context=TEST_USER_CONTEXT,
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

    async def mock_select_tool(question, user_context=None):
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
        user_context=None,
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
        "When will SYSTEM tablespace in FREEPDB1 reach 99%?",
        user_context=TEST_USER_CONTEXT,
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
        "Is the Docker Desktop Kubernetes cluster healthy?",
        user_context=TEST_USER_CONTEXT,
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
        "Which Kubernetes pods have high restart counts?",
        user_context=TEST_USER_CONTEXT,
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
        "Show pending Kubernetes pods.",
        user_context=TEST_USER_CONTEXT,
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
        "Show failed pods in namespace default.",
        user_context=TEST_USER_CONTEXT,
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
        user_context=None,
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
        },
        user_context=TEST_USER_CONTEXT,
    )

    assert result["status"] == "success"
    assert result["investigation"] == "kubernetes_pod_failure"
    assert result["cluster"] == "Docker Desktop"
    assert result["namespace"] == "default"
    assert result["pod"] == "validator"
    assert result["resolved_pod"] == "validator-abc123"
    assert result["evidence_summary"]["pod_details"]["availability"] == "available"
    assert result["evidence_summary"]["logs"]["availability"] == "available"
    assert result["evidence_summary"]["events"]["availability"] == "available"
    assert result["evidence_summary"]["events"]["record_count"] == 1

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
                "pod": "validator-abc123",
            },
        ),
        (
            "kubernetes",
            {
                "cluster": "Docker Desktop",
                "action": "events",
                "namespace": "default",
                "pod": "validator-abc123",
            },
        ),
    ]


@pytest.mark.asyncio
async def test_investigate_kubernetes_propagates_user_context_to_all_signals(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    user_context = UserContext(
        user_id="user-001",
        username="kubernetes-engineer",
        roles={"kubernetes_engineer"},
        permissions={"kubernetes.read"},
    )

    calls = []

    async def mock_execute_tool(
        tool_name,
        parameters=None,
        user_context=None,
    ):
        calls.append(
            (
                tool_name,
                parameters,
                user_context,
            )
        )
        return {
            "tool": "kubernetes",
            "status": "success",
            "data": {},
        }

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
        },
        user_context=user_context,
    )

    assert result["status"] == "success"
    assert len(calls) == 3
    assert [call[0] for call in calls] == [
        "kubernetes",
        "kubernetes",
        "kubernetes",
    ]
    assert [call[1]["action"] for call in calls] == [
        "pod_details",
        "logs",
        "events",
    ]
    assert all(
        call[2] == user_context
        for call in calls
    )


@pytest.mark.asyncio
async def test_investigate_kubernetes_returns_partial_when_signal_fails(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_execute_tool(
        tool_name,
        parameters=None,
        user_context=None,
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
        },
        user_context=TEST_USER_CONTEXT,
    )

    assert result["status"] == "partial"
    assert result["investigation"] == "kubernetes_pod_failure"
    assert len(result["signals"]) == 3
    assert (
        result["signals"]["logs"]["status"]
        == "error"
    )
    assert result["evidence_summary"]["logs"]["status"] == "error"
    assert result["evidence_summary"]["logs"]["availability"] == "unavailable"
    assert result["evidence_summary"]["events"]["availability"] == "available"




@pytest.mark.asyncio
async def test_investigate_kubernetes_marks_empty_logs_and_events(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_execute_tool(
        tool_name,
        parameters=None,
        user_context=None,
    ):
        action = parameters["action"]

        if action == "pod_details":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {"pod": "validator", "namespace": "default"},
            }

        if action == "logs":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "pod": "validator",
                    "namespace": "default",
                    "logs": {"content": ""},
                },
            }

        if action == "events":
            assert parameters["pod"] == "validator"
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "namespace": "default",
                    "events": {"count": 0, "items": []},
                },
            }

        raise AssertionError(f"Unexpected action: {action}")

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
        },
        user_context=TEST_USER_CONTEXT,
    )

    assert result["status"] == "success"
    assert result["evidence_summary"]["pod_details"]["availability"] == "available"
    assert result["evidence_summary"]["logs"]["availability"] == "empty"
    assert result["evidence_summary"]["events"]["availability"] == "empty"
    assert result["evidence_summary"]["events"]["record_count"] == 0

@pytest.mark.asyncio
async def test_process_investigation_applies_local_kubernetes_defaults(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question, user_context=None):
        return {
            "tool": "kubernetes",
            "parameters": {
                "pod": "validator",
            },
        }

    async def mock_investigate_kubernetes(
        parameters,
        user_context=None,
    ): 
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
        "Why is the validator pod failing?",
        user_context=TEST_USER_CONTEXT,
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

    async def mock_select_tool(question, user_context=None):
        return {
            "tool": "kubernetes",
            "parameters": {
                "action": "pods",
            },
        }

    async def mock_execute_tool(
        tool_name,
        parameters=None,
        user_context=None,
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
        "Show Kubernetes pods.",
        user_context=TEST_USER_CONTEXT,
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

@pytest.mark.asyncio
async def test_execute_tool_allows_database_engineer_for_database_tool(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    user_context = UserContext(
        user_id="user-001",
        username="db-engineer",
        roles={"database_engineer"},
        permissions={"database.read"},
    )

    tool = orchestrator.tool_registry.get("oracle_database")
    assert tool is not None

    async def mock_execute(request):
        return {
            "status": "success",
            "database": "FREEPDB1",
        }

    monkeypatch.setattr(
        tool,
        "execute",
        mock_execute,
    )

    result = await orchestrator.execute_tool(
        tool_name="oracle_database",
        parameters={"database": "FREEPDB1"},
        user_context=user_context,
    )

    assert result == {
        "status": "success",
        "database": "FREEPDB1",
    }


@pytest.mark.asyncio
async def test_execute_tool_denies_database_engineer_for_kubernetes_tool():
    orchestrator = AIOrchestrator()

    user_context = UserContext(
        user_id="user-001",
        username="db-engineer",
        roles={"database_engineer"},
        permissions={"database.read"},
    )

    result = await orchestrator.execute_tool(
        tool_name="kubernetes",
        parameters={
            "cluster": "Docker Desktop",
            "action": "pods",
        },
        user_context=user_context,
    )

    assert result["status"] == "error"
    assert result["error"] == "Permission denied: kubernetes.read"
@pytest.mark.asyncio
async def test_select_tool_denies_unauthorized_tool(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    user_context = UserContext(
        user_id="user-001",
        username="db-engineer",
        roles={"database_engineer"},
        permissions={"database.read"},
    )

    async def mock_generate_json(prompt):
        return {
            "tool": "kubernetes",
            "parameters": {
                "cluster": "Docker Desktop",
                "action": "pods",
            },
        }

    monkeypatch.setattr(
        orchestrator.llm,
        "generate_json",
        mock_generate_json,
    )

    result = await orchestrator.select_tool(
        "Show Kubernetes pods.",
        user_context=user_context,
    )

    assert result is None

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "question, expected_error",
    [
        (None, "Question must be a string."),
        (123, "Question must be a string."),
        ("", "Question must not be empty."),
        ("   ", "Question must not be empty."),
    ],
)
async def test_process_rejects_invalid_questions(
    question,
    expected_error,
):
    orchestrator = AIOrchestrator()

    with pytest.raises(ValueError, match=expected_error):
        await orchestrator.process(
            question=question,
            user_context=TEST_USER_CONTEXT,
        )
@pytest.mark.asyncio
@pytest.mark.parametrize("tool_status", ["error", "partial"])
async def test_process_propagates_tool_execution_status(
    monkeypatch,
    tool_status,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question, user_context=None):
        return {
            "tool": "oracle",
            "parameters": {},
        }

    async def mock_execute_tool(
        tool_name,
        parameters,
        user_context=None,
    ):
        return {
            "status": tool_status,
            "error": "Test execution result",
        }

    async def mock_search_knowledge(question, limit=5):
        return []

    async def mock_generate_answer(**kwargs):
        return "Test answer"

    monkeypatch.setattr(
        orchestrator, "select_tool", mock_select_tool
    )
    monkeypatch.setattr(
        orchestrator, "execute_tool", mock_execute_tool
    )
    monkeypatch.setattr(
        orchestrator, "search_knowledge", mock_search_knowledge
    )
    monkeypatch.setattr(
        orchestrator, "generate_answer", mock_generate_answer
    )

    result = await orchestrator.process(
        question="Check Oracle database status",
        user_context=TEST_USER_CONTEXT,
    )

    assert result["status"] == tool_status
    assert result["tool_result"]["status"] == tool_status

@pytest.mark.asyncio
async def test_process_handles_greeting_without_tools_or_rag(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def unexpected_call(*args, **kwargs):
        pytest.fail(
            "Greeting should not invoke tool selection, "
            "tool execution, or knowledge search."
        )

    monkeypatch.setattr(
        orchestrator,
        "select_tool",
        unexpected_call,
    )

    monkeypatch.setattr(
        orchestrator,
        "search_knowledge",
        unexpected_call,
    )

    monkeypatch.setattr(
        orchestrator,
        "generate_answer",
        unexpected_call,
    )

    result = await orchestrator.process(
        "Hi, how are you?",
        user_context=TEST_USER_CONTEXT,
    )

    assert result["status"] == "success"
    assert result["selected_tool"] is None
    assert result["parameters"] == {}
    assert result["tool_result"] is None
    assert result["knowledge_results"] == []
    assert "Hello!" in result["answer"]


@pytest.mark.asyncio
async def test_process_handles_thank_you_without_tools_or_rag(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def unexpected_call(*args, **kwargs):
        pytest.fail(
            "Conversational request should not invoke tools or RAG."
        )

    monkeypatch.setattr(
        orchestrator,
        "select_tool",
        unexpected_call,
    )

    monkeypatch.setattr(
        orchestrator,
        "search_knowledge",
        unexpected_call,
    )

    result = await orchestrator.process(
        "Thank you!",
        user_context=TEST_USER_CONTEXT,
    )

    assert result["status"] == "success"
    assert result["selected_tool"] is None
    assert result["knowledge_results"] == []
    assert "welcome" in result["answer"].lower()


# =============================================================
# KUBERNETES POD INVENTORY FORMATTER TESTS
# =============================================================

def test_kubernetes_inventory_groups_all_pods_by_namespace():
    result = {
        "status": "success",
        "data": {
            "cluster": "Docker Desktop",
            "pods": {
                "items": [
                    {
                        "namespace": "default",
                        "name": "app-pod",
                        "phase": "Running",
                        "restart_count": 2,
                    },
                    {
                        "namespace": "kube-system",
                        "name": "dns-pod",
                        "phase": "Running",
                        "restart_count": 1,
                    },
                    {
                        "namespace": "default",
                        "name": "worker-pod",
                        "phase": "Succeeded",
                        "restart_count": 0,
                    },
                ]
            },
        },
    }

    answer = AIOrchestrator._format_kubernetes_pod_inventory(
        question="Show all pods across every namespace",
        tool_name="kubernetes",
        tool_result=result,
    )

    assert "Total pods: 3" in answer
    assert "Namespace: default (2 pods)" in answer
    assert "Namespace: kube-system (1 pods)" in answer
    assert "| app-pod | Running | 2 |" in answer
    assert "| worker-pod | Succeeded | 0 |" in answer
    assert "| dns-pod | Running | 1 |" in answer


def test_kubernetes_inventory_handles_empty_pod_list():
    result = {
        "status": "success",
        "data": {
            "cluster": "Docker Desktop",
            "pods": {"items": []},
        },
    }

    answer = AIOrchestrator._format_kubernetes_pod_inventory(
        question="Show all pods",
        tool_name="kubernetes",
        tool_result=result,
    )

    assert "Total pods: 0" in answer
    assert "Pods by namespace:" in answer


def test_kubernetes_inventory_normalizes_restart_counts():
    result = {
        "status": "success",
        "data": {
            "pods": {
                "items": [
                    {
                        "namespace": "default",
                        "name": "negative-restarts",
                        "phase": "Running",
                        "restart_count": -5,
                    },
                    {
                        "namespace": "default",
                        "name": "invalid-restarts",
                        "phase": "Running",
                        "restart_count": "invalid",
                    },
                ]
            }
        },
    }

    answer = AIOrchestrator._format_kubernetes_pod_inventory(
        question="List pods",
        tool_name="kubernetes",
        tool_result=result,
    )

    assert "| negative-restarts | Running | 0 |" in answer
    assert "| invalid-restarts | Running | 0 |" in answer


def test_kubernetes_inventory_returns_none_for_invalid_data():
    invalid_results = [
        None,
        {},
        {"status": "error"},
        {"status": "success", "data": None},
        {"status": "success", "data": {"pods": None}},
        {"status": "success", "data": {"pods": {"items": None}}},
    ]

    for result in invalid_results:
        answer = AIOrchestrator._format_kubernetes_pod_inventory(
            question="Show all pods",
            tool_name="kubernetes",
            tool_result=result,
        )

        assert answer is None


def test_kubernetes_inventory_does_not_intercept_other_questions():
    result = {
        "status": "success",
        "data": {
            "pods": {
                "items": [
                    {
                        "namespace": "default",
                        "name": "app-pod",
                        "phase": "Running",
                        "restart_count": 0,
                    }
                ]
            }
        },
    }

    answer = AIOrchestrator._format_kubernetes_pod_inventory(
        question="Is my Kubernetes cluster healthy?",
        tool_name="kubernetes",
        tool_result=result,
    )

    assert answer is None


@pytest.mark.asyncio
async def test_investigate_kubernetes_uses_resolved_pod_for_logs_and_events(
    monkeypatch,
):
    orchestrator = AIOrchestrator()
    calls = []

    async def mock_execute_tool(
        tool_name,
        parameters=None,
        user_context=None,
    ):
        calls.append(dict(parameters))
        action = parameters["action"]

        if action == "pod_details":
            return {
                "tool": "kubernetes",
                "status": "success",
                "data": {
                    "pod": {
                        "name": "validator-59d58784f-bj6ss",
                        "namespace": "default",
                        "phase": "Pending",
                        "containers": [],
                    },
                },
            }

        return {
            "tool": "kubernetes",
            "status": "success",
            "data": {
                "pod": "validator-59d58784f-bj6ss",
                "namespace": "default",
                "logs": {"content": ""},
                "events": {"count": 0, "items": []},
            },
        }

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
        },
        user_context=TEST_USER_CONTEXT,
    )

    assert result["status"] == "success"
    assert result["pod"] == "validator"
    assert result["resolved_pod"] == "validator-59d58784f-bj6ss"
    assert calls[0]["action"] == "pod_details"
    assert calls[0]["pod"] == "validator"
    assert calls[1]["action"] == "logs"
    assert calls[1]["pod"] == "validator-59d58784f-bj6ss"
    assert calls[2]["action"] == "events"
    assert calls[2]["pod"] == "validator-59d58784f-bj6ss"

@pytest.mark.asyncio
async def test_generate_answer_identifies_explicit_ephemeral_storage_eviction(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    eviction_message = (
        "The node was low on resource: ephemeral-storage. "
        "Threshold quantity: 9400665051, "
        "available: 9111644Ki."
    )

    tool_result = {
        "status": "success",
        "investigation": "kubernetes_pod_failure",
        "namespace": "default",
        "pod": "validator-59d58784f-fc2hk",
        "resolved_pod": "validator-59d58784f-fc2hk",
        "diagnostic_facts": {
            "pod_eviction": {
                "reason": "Evicted",
                "message": eviction_message,
            }
        },
        "evidence_summary": {
            "pod_details": {
                "status": "success",
                "availability": "available",
                "eviction_evidence": {
                    "reason": "Evicted",
                    "message": eviction_message,
                },
            },
            "logs": {
                "status": "success",
                "availability": "empty",
            },
            "events": {
                "status": "success",
                "availability": "empty",
            },
        },
    }

    prompts = []

    async def mock_generate(prompt):
        prompts.append(prompt)

        if len(prompts) == 1:
            return "The pod was evicted due to ephemeral-storage pressure."

        return (
            "Root Cause\n"
            "The pod was evicted by kubelet due to "
            "node ephemeral-storage pressure.\n\n"
            "Evidence\n"
            "Pod status reason was Evicted. The status message "
            "identified ephemeral-storage pressure.\n\n"
            "Impact\n"
            "The validator pod entered Failed state.\n\n"
            "What Is Not Confirmed\n"
            "The workload responsible for storage consumption "
            "is not established."
        )

    monkeypatch.setattr(
        orchestrator.llm,
        "generate",
        mock_generate,
    )

    answer = await orchestrator.generate_answer(
        question=(
            "Investigate the validator pod failure."
        ),
        tool_name="kubernetes_investigation",
        tool_result=tool_result,
        knowledge_results=[],
    )

    assert len(prompts) == 2

    # First diagnostic prompt must contain the eviction evidence.
    assert "Evicted" in prompts[0]
    assert "ephemeral-storage" in prompts[0]
    assert "diagnostic_facts" in prompts[0]

    # Second formatting prompt must retain the same evidence.
    assert "Evicted" in prompts[1]
    assert "ephemeral-storage" in prompts[1]
    assert "Explicit eviction exception" in prompts[1]

    # Final answer must be the second-stage response.
    assert "Root Cause" in answer
    assert "ephemeral-storage pressure" in answer
    assert "What Is Not Confirmed" in answer

@pytest.mark.asyncio
async def test_generate_answer_does_not_infer_root_cause_without_eviction_evidence(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    tool_result = {
        "status": "success",
        "investigation": "kubernetes_pod_failure",
        "namespace": "default",
        "pod": "validator-test",
        "signals": {
            "pod_details": {
                "status": "success",
                "data": {
                    "pod": {
                        "name": "validator-test",
                        "phase": "Failed",
                        "reason": None,
                        "message": None,
                    }
                },
            }
        },
        "evidence_summary": {
            "pod_details": {
                "status": "success",
                "availability": "available",
            },
            "logs": {
                "status": "success",
                "availability": "empty",
            },
            "events": {
                "status": "success",
                "availability": "empty",
            },
        },
        "diagnostic_facts": {},
    }

    prompts = []

    async def mock_generate(prompt):
        prompts.append(prompt)

        if len(prompts) == 1:
            return "The pod is in Failed state, but its cause is unknown."

        return (
            "Root Cause\n"
            "The underlying root cause cannot be confirmed from "
            "the available evidence.\n\n"
            "Evidence\n"
            "The pod is in Failed state. No logs or events were returned.\n\n"
            "Impact\n"
            "The pod is in Failed state.\n\n"
            "What Is Not Confirmed\n"
            "The underlying reason for the failure is not established."
        )

    monkeypatch.setattr(
        orchestrator.llm,
        "generate",
        mock_generate,
    )

    answer = await orchestrator.generate_answer(
        question="Investigate validator-test.",
        tool_name="kubernetes_investigation",
        tool_result=tool_result,
        knowledge_results=[],
    )

    assert len(prompts) == 2
    assert "Explicit eviction exception" in prompts[1]
    assert (
        "The underlying root cause cannot be confirmed "
        "from the available evidence."
        in prompts[1]
    )
    assert (
        "The underlying root cause cannot be confirmed "
        "from the available evidence."
        in answer
    )

