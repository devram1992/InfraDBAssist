from datetime import datetime

import pytest

from backend.app.capacity.linux_capacity_collector import (
    LinuxCapacityCollector,
)


class FakeLinuxTool:
    def __init__(self, result: dict):
        self.result = result
        self.request = None

    def build_request(self, **kwargs) -> dict:
        self.request = kwargs
        return kwargs

    async def execute(self, request: dict) -> dict:
        return self.result


class FakeRepository:
    def __init__(self):
        self.measurements = []

    def record_measurement(
        self,
        *,
        observed_at,
        environment,
        source,
        target,
        resource,
        metric,
        value,
        unit,
        metadata,
    ):
        measurement_id = len(self.measurements) + 1

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
async def test_collect_disk_capacity_success():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-01",
                "disk_usage": "68%",
            },
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    result = await collector.collect_disk_capacity()

    assert result["status"] == "success"
    assert result["source"] == "linux"
    assert result["server"] == "DEV-SERVER-01"
    assert result["count"] == 1

    assert len(repository.measurements) == 1

    measurement = repository.measurements[0]

    assert measurement["source"] == "linux"
    assert measurement["target"] == "DEV-SERVER-01"
    assert measurement["resource"] == "disk"
    assert measurement["metric"] == "used_percent"
    assert measurement["value"] == 68.0
    assert measurement["unit"] == "percent"


@pytest.mark.asyncio
async def test_collect_disk_capacity_uses_supplied_server():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-02",
                "disk_usage": "72%",
            },
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    result = await collector.collect_disk_capacity(
        server="DEV-SERVER-02"
    )

    assert linux_tool.request == {
        "server": "DEV-SERVER-02",
    }

    assert result["server"] == "DEV-SERVER-02"
    assert repository.measurements[0]["value"] == 72.0


@pytest.mark.asyncio
async def test_collect_disk_capacity_accepts_numeric_percentage():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-03",
                "disk_usage": 81,
            },
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    result = await collector.collect_disk_capacity()

    assert result["measurements"][0]["used_percent"] == 81.0


@pytest.mark.asyncio
async def test_collect_disk_capacity_rejects_invalid_percentage():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-01",
                "disk_usage": "not-a-number",
            },
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    with pytest.raises(
        ValueError,
        match="Invalid disk usage percentage",
    ):
        await collector.collect_disk_capacity()


@pytest.mark.asyncio
async def test_collect_disk_capacity_rejects_percentage_above_100():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-01",
                "disk_usage": "101%",
            },
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        await collector.collect_disk_capacity()


@pytest.mark.asyncio
async def test_collect_disk_capacity_rejects_failed_tool():
    linux_tool = FakeLinuxTool(
        {
            "status": "error",
            "message": "Linux server unavailable",
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    with pytest.raises(
        RuntimeError,
        match="Linux disk capacity collection failed",
    ):
        await collector.collect_disk_capacity()


@pytest.mark.asyncio
async def test_collect_disk_capacity_uses_unknown_server_when_missing():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "disk_usage": "55%",
            },
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    result = await collector.collect_disk_capacity()

    assert result["server"] == "UNKNOWN"
    assert repository.measurements[0]["target"] == "UNKNOWN"


def test_parse_percentage():
    assert (
        LinuxCapacityCollector._parse_percentage("68%")
        == 68.0
    )

    assert (
        LinuxCapacityCollector._parse_percentage("72")
        == 72.0
    )

    assert (
        LinuxCapacityCollector._parse_percentage(81)
        == 81.0
    )


def test_parse_percentage_rejects_negative():
    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        LinuxCapacityCollector._parse_percentage("-1%")


def test_parse_percentage_rejects_empty():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        LinuxCapacityCollector._parse_percentage("")
