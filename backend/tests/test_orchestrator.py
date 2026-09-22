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