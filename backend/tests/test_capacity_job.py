import pytest

from backend.app.capacity import job


class FakeCollectorResult:
    def __init__(
        self,
        status: str = "success",
        count: int = 1,
    ):
        self.status = status
        self.count = count


@pytest.mark.asyncio
async def test_collect_capacity_all_collectors_success(monkeypatch):
    async def fake_oracle():
        return {
            "status": "success",
            "count": 4,
        }

    async def fake_linux():
        return {
            "status": "success",
            "count": 1,
        }

    monkeypatch.setattr(
        job,
        "collect_oracle_capacity",
        fake_oracle,
    )
    monkeypatch.setattr(
        job,
        "collect_linux_capacity",
        fake_linux,
    )

    result = await job.collect_capacity()

    assert result["status"] == "success"
    assert result["count"] == 5
    assert result["successful_collectors"] == 2
    assert result["failed_collectors"] == 0

    assert len(result["collections"]) == 2

    assert result["collections"][0]["source"] == "oracle"
    assert result["collections"][0]["status"] == "success"

    assert result["collections"][1]["source"] == "linux"
    assert result["collections"][1]["status"] == "success"


@pytest.mark.asyncio
async def test_collect_capacity_oracle_failure_linux_success(
    monkeypatch,
):
    async def fake_oracle():
        raise RuntimeError(
            "Oracle unavailable"
        )

    async def fake_linux():
        return {
            "status": "success",
            "count": 1,
        }

    monkeypatch.setattr(
        job,
        "collect_oracle_capacity",
        fake_oracle,
    )
    monkeypatch.setattr(
        job,
        "collect_linux_capacity",
        fake_linux,
    )

    result = await job.collect_capacity()

    assert result["status"] == "partial_success"
    assert result["count"] == 1
    assert result["successful_collectors"] == 1
    assert result["failed_collectors"] == 1

    oracle_result = result["collections"][0]

    assert oracle_result["source"] == "oracle"
    assert oracle_result["status"] == "error"
    assert oracle_result["error"] == "Oracle unavailable"

    linux_result = result["collections"][1]

    assert linux_result["source"] == "linux"
    assert linux_result["status"] == "success"


@pytest.mark.asyncio
async def test_collect_capacity_linux_failure_oracle_success(
    monkeypatch,
):
    async def fake_oracle():
        return {
            "status": "success",
            "count": 4,
        }

    async def fake_linux():
        raise RuntimeError(
            "Linux unavailable"
        )

    monkeypatch.setattr(
        job,
        "collect_oracle_capacity",
        fake_oracle,
    )
    monkeypatch.setattr(
        job,
        "collect_linux_capacity",
        fake_linux,
    )

    result = await job.collect_capacity()

    assert result["status"] == "partial_success"
    assert result["count"] == 4
    assert result["successful_collectors"] == 1
    assert result["failed_collectors"] == 1

    oracle_result = result["collections"][0]

    assert oracle_result["source"] == "oracle"
    assert oracle_result["status"] == "success"

    linux_result = result["collections"][1]

    assert linux_result["source"] == "linux"
    assert linux_result["status"] == "error"
    assert linux_result["error"] == "Linux unavailable"


@pytest.mark.asyncio
async def test_collect_capacity_all_collectors_fail(
    monkeypatch,
):
    async def fake_oracle():
        raise RuntimeError(
            "Oracle unavailable"
        )

    async def fake_linux():
        raise RuntimeError(
            "Linux unavailable"
        )

    monkeypatch.setattr(
        job,
        "collect_oracle_capacity",
        fake_oracle,
    )
    monkeypatch.setattr(
        job,
        "collect_linux_capacity",
        fake_linux,
    )

    result = await job.collect_capacity()

    assert result["status"] == "error"
    assert result["count"] == 0
    assert result["successful_collectors"] == 0
    assert result["failed_collectors"] == 2

    assert len(result["collections"]) == 2

    assert result["collections"][0]["source"] == "oracle"
    assert result["collections"][0]["status"] == "error"

    assert result["collections"][1]["source"] == "linux"
    assert result["collections"][1]["status"] == "error"


@pytest.mark.asyncio
async def test_collect_capacity_preserves_collector_result(
    monkeypatch,
):
    oracle_result = {
        "status": "success",
        "count": 4,
        "source": "oracle",
        "database": "FREEPDB1",
    }

    linux_result = {
        "status": "success",
        "count": 1,
        "source": "linux",
        "server": "DEV-SERVER-01",
    }

    async def fake_oracle():
        return oracle_result

    async def fake_linux():
        return linux_result

    monkeypatch.setattr(
        job,
        "collect_oracle_capacity",
        fake_oracle,
    )
    monkeypatch.setattr(
        job,
        "collect_linux_capacity",
        fake_linux,
    )

    result = await job.collect_capacity()

    assert (
        result["collections"][0]["result"]
        == oracle_result
    )

    assert (
        result["collections"][1]["result"]
        == linux_result
    )


@pytest.mark.asyncio
async def test_collect_capacity_handles_zero_measurements(
    monkeypatch,
):
    async def fake_oracle():
        return {
            "status": "success",
            "count": 0,
        }

    async def fake_linux():
        return {
            "status": "success",
            "count": 0,
        }

    monkeypatch.setattr(
        job,
        "collect_oracle_capacity",
        fake_oracle,
    )
    monkeypatch.setattr(
        job,
        "collect_linux_capacity",
        fake_linux,
    )

    result = await job.collect_capacity()

    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["successful_collectors"] == 2
    assert result["failed_collectors"] == 0