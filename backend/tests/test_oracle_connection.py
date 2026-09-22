from unittest.mock import MagicMock

import pytest

from backend.app.integrations.databases.oracle import OracleConnection


def test_oracle_connection_requires_configuration():
    connection = OracleConnection(
        config={
            "host": "",
            "service": "",
            "username": "",
            "password": "",
        }
    )

    with pytest.raises(
        ValueError,
        match="Oracle host is not configured.",
    ):
        connection._validate_config()


@pytest.mark.asyncio
async def test_oracle_health_check_when_disconnected():
    connection = OracleConnection()

    result = await connection.health_check()

    assert result == {
        "status": "disconnected",
        "database": "oracle",
    }


@pytest.mark.asyncio
async def test_oracle_execute_requires_connection():
    connection = OracleConnection()

    with pytest.raises(
        RuntimeError,
        match="Oracle connection is not established.",
    ):
        await connection.execute(
            "SELECT 1 FROM dual"
        )


@pytest.mark.asyncio
async def test_oracle_disconnect_when_not_connected():
    connection = OracleConnection()

    await connection.disconnect()

    assert connection.connection is None


@pytest.mark.asyncio
async def test_oracle_execute_rejects_write_query():
    connection = OracleConnection()
    connection.connection = MagicMock()

    with pytest.raises(
        ValueError,
        match="only permits read-only SELECT statements",
    ):
        await connection.execute(
            "DELETE FROM test_table"
        )

    connection.connection.cursor.assert_not_called()


@pytest.mark.asyncio
async def test_oracle_execute_rejects_multiple_statements():
    connection = OracleConnection()
    connection.connection = MagicMock()

    with pytest.raises(
        ValueError,
        match="only permits a single SQL statement",
    ):
        await connection.execute(
            "SELECT 1 FROM dual; DELETE FROM test_table"
        )

    connection.connection.cursor.assert_not_called()


@pytest.mark.asyncio
async def test_oracle_execute_rejects_select_for_update():
    connection = OracleConnection()
    connection.connection = MagicMock()

    with pytest.raises(
        ValueError,
        match="does not permit SELECT FOR UPDATE",
    ):
        await connection.execute(
            "SELECT status FROM v$instance FOR UPDATE"
        )

    connection.connection.cursor.assert_not_called()


@pytest.mark.asyncio
async def test_oracle_execute_accepts_select_query():
    connection = OracleConnection()

    cursor = MagicMock()
    cursor.description = [
        ("STATUS",)
    ]
    cursor.fetchall.return_value = [
        ("OPEN",)
    ]

    connection.connection = MagicMock()
    connection.connection.cursor.return_value = cursor

    result = await connection.execute(
        "SELECT status FROM v$instance"
    )

    assert result == [
        {
            "status": "OPEN",
        }
    ]

    connection.connection.cursor.assert_called_once()

    cursor.execute.assert_called_once_with(
        "SELECT status FROM v$instance",
        {},
    )

    cursor.close.assert_called_once()


@pytest.mark.asyncio
async def test_oracle_execute_accepts_select_query_with_trailing_semicolon():
    connection = OracleConnection()

    cursor = MagicMock()
    cursor.description = [
        ("STATUS",)
    ]
    cursor.fetchall.return_value = [
        ("OPEN",)
    ]

    connection.connection = MagicMock()
    connection.connection.cursor.return_value = cursor

    result = await connection.execute(
        "SELECT status FROM v$instance;"
    )

    assert result == [
        {
            "status": "OPEN",
        }
    ]

    cursor.execute.assert_called_once_with(
        "SELECT status FROM v$instance;",
        {},
    )

    cursor.close.assert_called_once()