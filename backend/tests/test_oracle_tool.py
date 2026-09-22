from unittest.mock import AsyncMock

import pytest

from backend.app.config.settings import Settings
from backend.app.tools.oracle.tool import OracleTool


def test_oracle_tool_build_request_uses_configured_database(
    monkeypatch,
):
    monkeypatch.setattr(
        Settings,
        "oracle_service",
        "FREEPDB1",
    )

    connection = AsyncMock()
    tool = OracleTool(connection=connection)

    result = tool.build_request()

    assert result == {
        "database": "FREEPDB1",
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
async def test_oracle_tool_execute_returns_health_summary():
    connection = AsyncMock()

    connection.execute.side_effect = [
        [
            {
                "instance_name": "FREE",
                "host_name": "oracle-host",
                "status": "OPEN",
                "version": "23.0.0.0.0",
            }
        ],
        [
            {
                "name": "FREE",
                "open_mode": "READ WRITE",
                "database_role": "PRIMARY",
            }
        ],
        [
            {
                "container_name": "FREEPDB1",
                "db_name": "FREEPDB1",
            }
        ],
    ]

    tool = OracleTool(connection=connection)

    result = await tool.execute(
        {
            "database": "FREEPDB1",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "FREEPDB1",
        "state": "OPEN",
        "instance": {
            "instance_name": "FREE",
            "host_name": "oracle-host",
            "status": "OPEN",
            "version": "23.0.0.0.0",
        },
        "database_info": {
            "name": "FREE",
            "open_mode": "READ WRITE",
            "database_role": "PRIMARY",
        },
        "container": {
            "container_name": "FREEPDB1",
            "db_name": "FREEPDB1",
        },
    }

    connection.connect.assert_awaited_once()

    assert connection.execute.await_count == 3

    connection.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_oracle_tool_execute_returns_unknown_when_queries_are_empty():
    connection = AsyncMock()

    connection.execute.side_effect = [
        [],
        [],
        [],
    ]

    tool = OracleTool(connection=connection)

    result = await tool.execute(
        {
            "database": "FREEPDB1",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "FREEPDB1",
        "state": "UNKNOWN",
        "instance": {
            "instance_name": "UNKNOWN",
            "host_name": "UNKNOWN",
            "status": "UNKNOWN",
            "version": "UNKNOWN",
        },
        "database_info": {
            "name": "UNKNOWN",
            "open_mode": "UNKNOWN",
            "database_role": "UNKNOWN",
        },
        "container": {
            "container_name": "UNKNOWN",
            "db_name": "UNKNOWN",
        },
    }

    connection.connect.assert_awaited_once()

    assert connection.execute.await_count == 3

    connection.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_oracle_tool_execute_disconnects_when_query_fails():
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
                "database": "FREEPDB1",
            }
        )

    connection.connect.assert_awaited_once()

    connection.execute.assert_awaited_once()

    connection.disconnect.assert_awaited_once()