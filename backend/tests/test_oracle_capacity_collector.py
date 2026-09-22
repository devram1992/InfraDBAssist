from datetime import datetime

import pytest

from backend.app.capacity.oracle_collector import (
    OracleCapacityCollector,
)


class FakeOracleTool:
    def __init__(
        self,
        result=None,
        error=None,
    ):
        self.result = result
        self.error = error
        self.requests = []

    def build_request(
        self,
        **kwargs,
    ):
        self.requests.append(
            kwargs
        )

        return kwargs

    async def execute(
        self,
        request,
    ):
        if self.error is not None:
            raise self.error

        return self.result


class FakeCapacityRepository:
    def __init__(self):
        self.measurements = []

    def record_measurement(
        self,
        observed_at,
        environment,
        source,
        target,
        resource,
        metric,
        value,
        unit,
        metadata=None,
    ):
        measurement_id = (
            len(self.measurements)
            + 1
        )

        self.measurements.append(
            {
                "id": measurement_id,
                "observed_at": observed_at,
                "environment": environment,
                "source": source,
                "target": target,
                "resource": resource,
                "metric": metric,
                "value": value,
                "unit": unit,
                "metadata": metadata,
            }
        )

        return measurement_id


@pytest.mark.asyncio
async def test_collect_tablespace_capacity():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
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
                    "used_mb": 418.75,
                    "free_mb": 21.25,
                    "used_percent": 95.17,
                },
            ],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    result = (
        await collector.collect_tablespace_capacity(
            database="FREEPDB1",
        )
    )

    assert result["status"] == "success"
    assert result["source"] == "oracle"
    assert result["database"] == "FREEPDB1"
    assert result["metric"] == "capacity"
    assert result["count"] == 2

    # Two metrics per tablespace:
    # used_percent + used_mb
    assert len(
        repository.measurements
    ) == 4

    assert (
        repository.measurements[0]["resource"]
        == "SYSTEM"
    )

    assert (
        repository.measurements[0]["metric"]
        == "used_percent"
    )

    assert (
        repository.measurements[0]["unit"]
        == "percent"
    )

    assert (
        repository.measurements[0]["value"]
        == 98.52
    )

    assert (
        repository.measurements[1]["resource"]
        == "SYSTEM"
    )

    assert (
        repository.measurements[1]["metric"]
        == "used_mb"
    )

    assert (
        repository.measurements[1]["unit"]
        == "MB"
    )

    assert (
        repository.measurements[1]["value"]
        == 295.56
    )

    assert (
        repository.measurements[2]["resource"]
        == "SYSAUX"
    )

    assert (
        repository.measurements[2]["metric"]
        == "used_percent"
    )

    assert (
        repository.measurements[2]["value"]
        == 95.17
    )

    assert (
        repository.measurements[3]["resource"]
        == "SYSAUX"
    )

    assert (
        repository.measurements[3]["metric"]
        == "used_mb"
    )

    assert (
        repository.measurements[3]["value"]
        == 418.75
    )


@pytest.mark.asyncio
async def test_collect_uses_tablespace_action():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
            "tablespaces": [],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    await collector.collect_tablespace_capacity(
        database="FREEPDB1",
    )

    assert oracle_tool.requests == [
        {
            "database": "FREEPDB1",
            "action": "tablespace",
        }
    ]


@pytest.mark.asyncio
async def test_collect_handles_empty_tablespace_result():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
            "tablespaces": [],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    result = (
        await collector.collect_tablespace_capacity(
            database="FREEPDB1",
        )
    )

    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["measurements"] == []

    assert (
        repository.measurements
        == []
    )


@pytest.mark.asyncio
async def test_collect_rejects_failed_oracle_result():
    oracle_tool = FakeOracleTool(
        result={
            "status": "error",
            "message": "Oracle unavailable",
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    with pytest.raises(
        RuntimeError,
        match="Oracle tablespace collection failed",
    ):
        await collector.collect_tablespace_capacity(
            database="FREEPDB1",
        )

    assert (
        repository.measurements
        == []
    )


@pytest.mark.asyncio
async def test_collect_stores_metadata():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
            "tablespaces": [
                {
                    "tablespace_name": "USERS",
                    "total_mb": 7.0,
                    "used_mb": 6.06,
                    "free_mb": 0.94,
                    "used_percent": 86.57,
                },
            ],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    await collector.collect_tablespace_capacity(
        database="FREEPDB1",
    )

    assert len(
        repository.measurements
    ) == 2

    used_percent = (
        repository.measurements[0]
    )

    used_mb = (
        repository.measurements[1]
    )

    assert (
        used_percent["metric"]
        == "used_percent"
    )

    assert (
        used_percent["metadata"]
        == {
            "total_mb": 7.0,
            "free_mb": 0.94,
            "used_mb": 6.06,
        }
    )

    assert (
        used_mb["metric"]
        == "used_mb"
    )

    assert (
        used_mb["metadata"]
        == {
            "total_mb": 7.0,
            "free_mb": 0.94,
            "used_percent": 86.57,
        }
    )


@pytest.mark.asyncio
async def test_collect_generates_timestamp():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
            "tablespaces": [
                {
                    "tablespace_name": "SYSTEM",
                    "total_mb": 300.0,
                    "used_mb": 295.56,
                    "free_mb": 4.44,
                    "used_percent": 98.52,
                },
            ],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    result = (
        await collector.collect_tablespace_capacity(
            database="FREEPDB1",
        )
    )

    assert isinstance(
        result["observed_at"],
        datetime,
    )

    assert (
        repository.measurements[0][
            "observed_at"
        ]
        == result["observed_at"]
    )

    assert (
        repository.measurements[1][
            "observed_at"
        ]
        == result["observed_at"]
    )


@pytest.mark.asyncio
async def test_collect_persists_both_metrics_for_each_tablespace():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
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
                    "used_mb": 418.75,
                    "free_mb": 21.25,
                    "used_percent": 95.17,
                },
                {
                    "tablespace_name": "USERS",
                    "total_mb": 7.0,
                    "used_mb": 6.06,
                    "free_mb": 0.94,
                    "used_percent": 86.57,
                },
            ],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    result = (
        await collector.collect_tablespace_capacity(
            database="FREEPDB1",
        )
    )

    assert result["count"] == 3

    assert len(
        repository.measurements
    ) == 6

    resources = [
        measurement["resource"]
        for measurement
        in repository.measurements
    ]

    metrics = [
        measurement["metric"]
        for measurement
        in repository.measurements
    ]

    assert resources == [
        "SYSTEM",
        "SYSTEM",
        "SYSAUX",
        "SYSAUX",
        "USERS",
        "USERS",
    ]

    assert metrics == [
        "used_percent",
        "used_mb",
        "used_percent",
        "used_mb",
        "used_percent",
        "used_mb",
    ]


@pytest.mark.asyncio
async def test_collect_stores_used_mb_metric():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
            "tablespaces": [
                {
                    "tablespace_name": "SYSTEM",
                    "total_mb": 300.0,
                    "used_mb": 295.56,
                    "free_mb": 4.44,
                    "used_percent": 98.52,
                },
            ],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    result = (
        await collector.collect_tablespace_capacity(
            database="FREEPDB1",
        )
    )

    assert result["count"] == 1
    assert len(
        repository.measurements
    ) == 2

    used_mb = next(
        item
        for item in repository.measurements
        if item["metric"] == "used_mb"
    )

    assert used_mb["value"] == 295.56
    assert used_mb["unit"] == "MB"
    assert used_mb["resource"] == "SYSTEM"


@pytest.mark.asyncio
async def test_collect_returns_measurement_ids():
    oracle_tool = FakeOracleTool(
        result={
            "status": "success",
            "database": "FREEPDB1",
            "tablespaces": [
                {
                    "tablespace_name": "SYSTEM",
                    "total_mb": 300.0,
                    "used_mb": 295.56,
                    "free_mb": 4.44,
                    "used_percent": 98.52,
                },
            ],
        }
    )

    repository = (
        FakeCapacityRepository()
    )

    collector = OracleCapacityCollector(
        oracle_tool=oracle_tool,
        repository=repository,
    )

    result = (
        await collector.collect_tablespace_capacity(
            database="FREEPDB1",
        )
    )

    measurement = (
        result["measurements"][0]
    )

    assert (
        measurement[
            "used_percent_measurement_id"
        ]
        == 1
    )

    assert (
        measurement[
            "used_mb_measurement_id"
        ]
        == 2
    )