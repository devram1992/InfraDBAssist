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
        "action": "health",
    }


def test_oracle_tool_build_request_uses_requested_database():
    connection = AsyncMock()
    tool = OracleTool(connection=connection)

    result = tool.build_request(
        database="DEVDB",
    )

    assert result == {
        "database": "DEVDB",
        "action": "health",
    }


def test_oracle_tool_build_request_accepts_sessions_action():
    connection = AsyncMock()
    tool = OracleTool(connection=connection)

    result = tool.build_request(
        database="FREEPDB1",
        action="sessions",
    )

    assert result == {
        "database": "FREEPDB1",
        "action": "sessions",
    }


def test_oracle_tool_build_request_accepts_tablespace_action():
    connection = AsyncMock()
    tool = OracleTool(connection=connection)

    result = tool.build_request(
        database="FREEPDB1",
        action="tablespace",
    )

    assert result == {
        "database": "FREEPDB1",
        "action": "tablespace",
    }


def test_oracle_tool_build_request_rejects_unknown_action():
    connection = AsyncMock()
    tool = OracleTool(connection=connection)

    with pytest.raises(
        ValueError,
        match="Unsupported Oracle diagnostic action.",
    ):
        tool.build_request(
            database="FREEPDB1",
            action="invalid",
        )


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
            "action": "health",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "FREEPDB1",
        "action": "health",
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
async def test_oracle_tool_execute_returns_active_sessions():
    connection = AsyncMock()

    connection.execute.return_value = [
        {
            "sid": 101,
            "serial#": 12345,
            "username": "APPUSER",
            "status": "ACTIVE",
            "event": "SQL*Net message to client",
            "machine": "test-host",
            "program": "test-program",
        }
    ]

    tool = OracleTool(connection=connection)

    result = await tool.execute(
        {
            "database": "FREEPDB1",
            "action": "sessions",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "FREEPDB1",
        "action": "sessions",
        "sessions": [
            {
                "sid": 101,
                "serial#": 12345,
                "username": "APPUSER",
                "status": "ACTIVE",
                "event": "SQL*Net message to client",
                "machine": "test-host",
                "program": "test-program",
            }
        ],
        "count": 1,
    }

    connection.connect.assert_awaited_once()
    connection.execute.assert_awaited_once()
    connection.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_oracle_tool_execute_returns_tablespace_usage():
    connection = AsyncMock()

    connection.execute.return_value = [
        {
            "tablespace_name": "SYSTEM",
            "total_mb": 300,
            "free_mb": 4.44,
        },
        {
            "tablespace_name": "SYSAUX",
            "total_mb": 440,
            "free_mb": 26.5,
        },
    ]

    tool = OracleTool(connection=connection)

    result = await tool.execute(
        {
            "database": "FREEPDB1",
            "action": "tablespace",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "FREEPDB1",
        "action": "tablespace",
        "tablespaces": [
            {
                "tablespace_name": "SYSTEM",
                "total_mb": 300.0,
                "used_mb": 295.56,
                "free_mb": 4.44,
                "used_percent": 98.52,
            },
            {
                "tablespace_name": "SYSAUX",
                "total_mb": 440.0,
                "used_mb": 413.5,
                "free_mb": 26.5,
                "used_percent": 93.98,
            },
        ],
        "count": 2,
    }

    connection.connect.assert_awaited_once()
    connection.execute.assert_awaited_once()
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
            "action": "health",
        }
    )

    assert result == {
        "tool": "oracle_database",
        "status": "success",
        "database": "FREEPDB1",
        "action": "health",
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
                "action": "health",
            }
        )

    connection.connect.assert_awaited_once()
    connection.execute.assert_awaited_once()
    connection.disconnect.assert_awaited_once()
