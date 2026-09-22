from unittest.mock import AsyncMock

import pytest

from backend.app.tools.oracle.tool import OracleTool


def test_oracle_tool_build_request_uses_default_database():
    connection = AsyncMock()
    tool = OracleTool(connection=connection)

    result = tool.build_request()

    assert result == {
        "database": "PRODDB",
    }


def test_oracle_tool_build_request_uses_requested_database():
    connection = AsyncMock()
    tool = OracleTool(connection=connection)

    result = tool.build_request(
        database="DEVDB",
    )

    assert result == {
        "database": "DEVDB",
    }


@pytest.mark.asyncio
async def test_oracle_tool_execute_returns_instance_state():
    connection = AsyncMock()

    connection.execute.return_value = [
        {
            "status": "OPEN",
        }
    ]

    tool = OracleTool(connection=connection)

    result = await tool.execute(
        {
            "database": "DEVDB",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "DEVDB",
        "state": "OPEN",
    }

    connection.connect.assert_awaited_once()

    connection.execute.assert_awaited_once_with(
        "SELECT status FROM v$instance"
    )

    connection.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_oracle_tool_execute_returns_unknown_when_no_rows():
    connection = AsyncMock()

    connection.execute.return_value = []

    tool = OracleTool(connection=connection)

    result = await tool.execute(
        {
            "database": "DEVDB",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "DEVDB",
        "state": "UNKNOWN",
    }

    connection.connect.assert_awaited_once()
    connection.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_oracle_tool_disconnects_when_query_fails():
    connection = AsyncMock()

    connection.execute.side_effect = RuntimeError(
        "Oracle query failed"
    )

    tool = OracleTool(connection=connection)

    with pytest.raises(
        RuntimeError,
        match="Oracle query failed",
    ):
        await tool.execute(
            {
                "database": "DEVDB",
            }
        )

    connection.connect.assert_awaited_once()
    connection.execute.assert_awaited_once()
    connection.disconnect.assert_awaited_once()
