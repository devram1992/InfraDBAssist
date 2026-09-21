import pytest

from backend.app.integrations.databases.oracle import OracleConnection


def test_oracle_connection_requires_configuration():
    connection = OracleConnection()

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
