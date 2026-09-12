import pytest

from backend.app.ai.orchestrator import AIOrchestrator


@pytest.mark.asyncio
async def test_process_supports_knowledge_only_question(
    monkeypatch,
):
    orchestrator = AIOrchestrator()

    async def mock_select_tool(question):
        return None

    async def mock_search_knowledge(question, limit=5):
        return [
            {
                "title": "database_backup",
                "source_type": "sop",
                "similarity": 0.85,
                "content": "Verify backup completion and archive logs.",
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

        return "Use the database backup SOP to verify completion."

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

    async def mock_search_knowledge(question, limit=5):
        return [
            {
                "title": "oracle_performance",
                "source_type": "runbook",
                "similarity": 0.90,
                "content": "Review active sessions and wait events.",
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
    assert result["selected_tool"] == "oracle_database"
    assert result["parameters"] == {
        "database": "PRODDB",
    }
    assert result["tool_result"]["database"] == "PRODDB"
    assert len(result["knowledge_results"]) == 1
    assert result["answer"] == "PRODDB is OPEN."
