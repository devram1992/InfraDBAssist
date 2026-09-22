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


def filesystem_payload():
    return {
        "status": "success",
        "data": {
            "server": "DEV-SERVER-01",
            "disk_usage": "70%",
            "filesystems": [
                {
                    "filesystem": "/dev/root",
                    "mount_point": "/",
                    "total_mb": 102400.0,
                    "used_mb": 71680.0,
                    "available_mb": 30720.0,
                    "used_percent": 70.0,
                },
                {
                    "filesystem": "/dev/data",
                    "mount_point": "/data",
                    "total_mb": 204800.0,
                    "used_mb": 102400.0,
                    "available_mb": 102400.0,
                    "used_percent": 50.0,
                },
                {
                    "filesystem": "/dev/u01",
                    "mount_point": "/u01",
                    "total_mb": 51200.0,
                    "used_mb": 40960.0,
                    "available_mb": 10240.0,
                    "used_percent": 80.0,
                },
            ],
        },
    }


@pytest.mark.asyncio
async def test_collect_disk_capacity_collects_each_filesystem():
    linux_tool = FakeLinuxTool(
        filesystem_payload()
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

    # Three filesystems were collected.
    assert result["count"] == 3
    assert len(result["measurements"]) == 3

    resources = [
        measurement["resource"]
        for measurement in result["measurements"]
    ]

    assert resources == [
        "/",
        "/data",
        "/u01",
    ]


@pytest.mark.asyncio
async def test_collect_disk_capacity_stores_used_percent_and_used_mb():
    linux_tool = FakeLinuxTool(
        filesystem_payload()
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    result = await collector.collect_disk_capacity()

    assert result["count"] == 3

    # Two measurements per filesystem:
    # used_percent + used_mb.
    assert len(repository.measurements) == 6

    root_measurements = [
        measurement
        for measurement in repository.measurements
        if measurement["resource"] == "/"
    ]

    assert len(root_measurements) == 2

    percent_measurement = next(
        measurement
        for measurement in root_measurements
        if measurement["metric"] == "used_percent"
    )

    mb_measurement = next(
        measurement
        for measurement in root_measurements
        if measurement["metric"] == "used_mb"
    )

    assert percent_measurement["value"] == 70.0
    assert percent_measurement["unit"] == "percent"

    assert mb_measurement["value"] == 71680.0
    assert mb_measurement["unit"] == "MB"


@pytest.mark.asyncio
async def test_collect_disk_capacity_stores_filesystem_metadata():
    linux_tool = FakeLinuxTool(
        filesystem_payload()
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    await collector.collect_disk_capacity()

    root_percent = next(
        measurement
        for measurement in repository.measurements
        if (
            measurement["resource"] == "/"
            and measurement["metric"] == "used_percent"
        )
    )

    assert root_percent["metadata"] == {
        "filesystem": "/dev/root",
        "total_mb": 102400.0,
        "available_mb": 30720.0,
        "used_mb": 71680.0,
        "used_percent": 70.0,
    }


@pytest.mark.asyncio
async def test_collect_disk_capacity_collects_u01_independently():
    linux_tool = FakeLinuxTool(
        filesystem_payload()
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    result = await collector.collect_disk_capacity()

    u01 = [
        measurement
        for measurement in result["measurements"]
        if measurement["resource"] == "/u01"
    ]

    assert len(u01) == 1

    assert u01[0]["used_percent"] == 80.0
    assert u01[0]["used_mb"] == 40960.0
    assert u01[0]["total_mb"] == 51200.0
    assert u01[0]["available_mb"] == 10240.0


@pytest.mark.asyncio
async def test_collect_disk_capacity_uses_supplied_server():
    linux_tool = FakeLinuxTool(
        filesystem_payload()
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

    assert result["server"] == "DEV-SERVER-01"
    assert repository.measurements[0]["target"] == (
        "DEV-SERVER-01"
    )


@pytest.mark.asyncio
async def test_collect_disk_capacity_rejects_invalid_percentage():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-01",
                "filesystems": [
                    {
                        "filesystem": "/dev/root",
                        "mount_point": "/",
                        "total_mb": 100.0,
                        "used_mb": 60.0,
                        "available_mb": 40.0,
                        "used_percent": "not-a-number",
                    }
                ],
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
                "filesystems": [
                    {
                        "filesystem": "/dev/root",
                        "mount_point": "/",
                        "total_mb": 100.0,
                        "used_mb": 101.0,
                        "available_mb": 0.0,
                        "used_percent": "101%",
                    }
                ],
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
async def test_collect_disk_capacity_rejects_negative_used_mb():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-01",
                "filesystems": [
                    {
                        "filesystem": "/dev/root",
                        "mount_point": "/",
                        "total_mb": 100.0,
                        "used_mb": -1.0,
                        "available_mb": 101.0,
                        "used_percent": 1.0,
                    }
                ],
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
        match="used_mb cannot be negative",
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
async def test_collect_disk_capacity_rejects_empty_filesystem_result():
    linux_tool = FakeLinuxTool(
        {
            "status": "success",
            "data": {
                "server": "DEV-SERVER-01",
                "filesystems": [],
            },
        }
    )

    repository = FakeRepository()

    collector = LinuxCapacityCollector(
        linux_tool=linux_tool,
        repository=repository,
    )

    with pytest.raises(
        RuntimeError,
        match="no filesystem measurements",
    ):
        await collector.collect_disk_capacity()


@pytest.mark.asyncio
async def test_collect_disk_capacity_uses_legacy_disk_usage():
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
    assert result["count"] == 1

    assert result["measurements"][0]["resource"] == "disk"
    assert result["measurements"][0]["used_percent"] == 68.0

    assert len(repository.measurements) == 1
    assert repository.measurements[0]["metric"] == (
        "used_percent"
    )
    assert repository.measurements[0]["unit"] == "percent"


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
        LinuxCapacityCollector._parse_percentage(
            "-1%"
        )


def test_parse_percentage_rejects_empty():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        LinuxCapacityCollector._parse_percentage(
            ""
        )


def test_parse_number():
    assert (
        LinuxCapacityCollector._parse_number(
            "1024.5",
            "total_mb",
        )
        == 1024.5
    )

    assert (
        LinuxCapacityCollector._parse_number(
            500,
            "used_mb",
        )
        == 500.0
    )


def test_parse_number_rejects_invalid_value():
    with pytest.raises(
        ValueError,
        match="Invalid used_mb",
    ):
        LinuxCapacityCollector._parse_number(
            "invalid",
            "used_mb",
        )


def test_parse_number_rejects_negative_value():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        LinuxCapacityCollector._parse_number(
            -10,
            "used_mb",
        )