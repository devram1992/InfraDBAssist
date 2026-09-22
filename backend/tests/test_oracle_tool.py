import pytest

from backend.app.config.settings import Settings
from backend.app.tools.oracle.tool import OracleTool


class FakeConnection:
    def __init__(
        self,
        responses=None,
        error=None,
    ):
        self.responses = responses or []
        self.error = error
        self.connected = False
        self.disconnected = False
        self.executed_queries = []

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.disconnected = True

    async def execute(
        self,
        query,
        parameters=None,
    ):
        self.executed_queries.append(query)

        if self.error is not None:
            raise self.error

        if self.responses:
            return self.responses.pop(0)

        return []


def test_build_request_uses_configured_database(
    monkeypatch,
):
    monkeypatch.setattr(
        Settings,
        "oracle_service",
        "FREEPDB1",
    )

    connection = FakeConnection()

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request()

    assert request == {
        "database": "FREEPDB1",
        "action": "health",
    }


def test_build_request_uses_explicit_database():
    connection = FakeConnection()

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="TESTPDB",
    )

    assert request == {
        "database": "TESTPDB",
        "action": "health",
    }


def test_build_request_sessions_action():
    connection = FakeConnection()

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="sessions",
    )

    assert request == {
        "database": "FREEPDB1",
        "action": "sessions",
    }


def test_build_request_tablespace_action():
    connection = FakeConnection()

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="tablespace",
    )

    assert request == {
        "database": "FREEPDB1",
        "action": "tablespace",
    }


def test_build_request_blocking_sessions_action():
    connection = FakeConnection()

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="blocking_sessions",
    )

    assert request == {
        "database": "FREEPDB1",
        "action": "blocking_sessions",
    }


def test_build_request_rejects_invalid_action():
    connection = FakeConnection()

    tool = OracleTool(
        connection=connection,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported Oracle diagnostic action",
    ):
        tool.build_request(
            database="FREEPDB1",
            action="drop_database",
        )


@pytest.mark.asyncio
async def test_health_summary():
    connection = FakeConnection(
        responses=[
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
                    "db_name": "FREE",
                }
            ],
        ]
    )

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="health",
    )

    result = await tool.execute(
        request
    )

    assert connection.connected is True
    assert connection.disconnected is True

    assert result["status"] == "success"
    assert result["database"] == "FREEPDB1"
    assert result["action"] == "health"
    assert result["state"] == "OPEN"

    assert result["instance"]["instance_name"] == "FREE"
    assert result["instance"]["host_name"] == "oracle-host"
    assert result["instance"]["version"] == "23.0.0.0.0"

    assert result["database_info"]["name"] == "FREE"
    assert result["database_info"]["open_mode"] == "READ WRITE"
    assert result["database_info"]["database_role"] == "PRIMARY"

    assert result["container"]["container_name"] == "FREEPDB1"
    assert result["container"]["db_name"] == "FREE"


@pytest.mark.asyncio
async def test_health_returns_unknown_when_no_rows():
    connection = FakeConnection(
        responses=[
            [],
            [],
            [],
        ]
    )

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="health",
    )

    result = await tool.execute(
        request
    )

    assert result["status"] == "success"
    assert result["state"] == "UNKNOWN"

    assert result["instance"]["instance_name"] == "UNKNOWN"
    assert result["instance"]["host_name"] == "UNKNOWN"
    assert result["instance"]["status"] == "UNKNOWN"
    assert result["instance"]["version"] == "UNKNOWN"

    assert result["database_info"]["name"] == "UNKNOWN"
    assert result["database_info"]["open_mode"] == "UNKNOWN"
    assert result["database_info"]["database_role"] == "UNKNOWN"

    assert result["container"]["container_name"] == "UNKNOWN"
    assert result["container"]["db_name"] == "UNKNOWN"


@pytest.mark.asyncio
async def test_active_sessions():
    rows = [
        {
            "sid": 101,
            "serial#": 55,
            "username": "APPUSER",
            "status": "ACTIVE",
            "event": "db file sequential read",
            "machine": "app-server",
            "program": "JDBC",
        },
        {
            "sid": 102,
            "serial#": 77,
            "username": "APPUSER",
            "status": "ACTIVE",
            "event": "SQL*Net message from client",
            "machine": "app-server-2",
            "program": "JDBC",
        },
    ]

    connection = FakeConnection(
        responses=[rows]
    )

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="sessions",
    )

    result = await tool.execute(
        request
    )

    assert result["status"] == "success"
    assert result["database"] == "FREEPDB1"
    assert result["action"] == "sessions"
    assert result["count"] == 2
    assert result["sessions"] == rows


@pytest.mark.asyncio
async def test_tablespace_usage():
    rows = [
        {
            "tablespace_name": "SYSTEM",
            "total_mb": 300,
            "free_mb": 4.44,
        },
        {
            "tablespace_name": "SYSAUX",
            "total_mb": 440,
            "free_mb": 26.44,
        },
    ]

    connection = FakeConnection(
        responses=[rows]
    )

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="tablespace",
    )

    result = await tool.execute(
        request
    )

    assert result["status"] == "success"
    assert result["database"] == "FREEPDB1"
    assert result["action"] == "tablespace"
    assert result["count"] == 2

    system = result["tablespaces"][0]

    assert system["tablespace_name"] == "SYSTEM"
    assert system["total_mb"] == 300.0
    assert system["free_mb"] == 4.44
    assert system["used_mb"] == 295.56
    assert system["used_percent"] == 98.52


@pytest.mark.asyncio
async def test_blocking_sessions():
    rows = [
        {
            "blocked_sid": 101,
            "blocked_serial": 55,
            "blocked_username": "APPUSER",
            "blocked_event": (
                "enq: TX - row lock contention"
            ),
            "wait_seconds": 120,
            "blocker_sid": 88,
            "blocker_serial": 12,
            "blocker_username": "APPUSER",
            "blocker_machine": "app-server",
            "blocker_program": "JDBC",
        }
    ]

    connection = FakeConnection(
        responses=[rows]
    )

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="blocking_sessions",
    )

    result = await tool.execute(
        request
    )

    assert result["status"] == "success"
    assert result["database"] == "FREEPDB1"
    assert result["action"] == "blocking_sessions"
    assert result["count"] == 1

    assert (
        result["blocking_sessions"][0]["blocked_sid"]
        == 101
    )

    assert (
        result["blocking_sessions"][0]["blocker_sid"]
        == 88
    )

    assert (
        result["blocking_sessions"][0]["wait_seconds"]
        == 120
    )


@pytest.mark.asyncio
async def test_disconnect_on_query_failure():
    connection = FakeConnection(
        error=RuntimeError(
            "Oracle query failed"
        )
    )

    tool = OracleTool(
        connection=connection,
    )

    request = tool.build_request(
        database="FREEPDB1",
        action="health",
    )

    with pytest.raises(
        RuntimeError,
        match="Oracle query failed",
    ):
        await tool.execute(
            request
        )

    assert connection.connected is True
    assert connection.disconnected is True