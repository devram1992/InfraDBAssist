import pytest

from backend.app.capacity import job
from backend.app.capacity.scheduler import CapacityScheduler


def test_scheduler_uses_configured_interval(monkeypatch):
    monkeypatch.setenv(
        "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS",
        "600",
    )

    scheduler = CapacityScheduler()

    assert scheduler.interval_seconds == 600
    assert scheduler.running is False


def test_scheduler_uses_default_interval(monkeypatch):
    monkeypatch.delenv(
        "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS",
        raising=False,
    )

    scheduler = CapacityScheduler()

    assert (
        scheduler.interval_seconds
        == CapacityScheduler.DEFAULT_INTERVAL_SECONDS
    )


def test_scheduler_rejects_invalid_interval(monkeypatch):
    monkeypatch.setenv(
        "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS",
        "abc",
    )

    with pytest.raises(
        ValueError,
        match="must be a valid integer",
    ):
        CapacityScheduler()


def test_scheduler_rejects_zero_interval(monkeypatch):
    monkeypatch.setenv(
        "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="must be greater than 0",
    ):
        CapacityScheduler()


def test_scheduler_rejects_negative_interval(monkeypatch):
    monkeypatch.setenv(
        "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS",
        "-10",
    )

    with pytest.raises(
        ValueError,
        match="must be greater than 0",
    ):
        CapacityScheduler()


def test_get_oracle_capacity_target_uses_configured_target(monkeypatch):
    monkeypatch.setenv(
        "INFRADB_CAPACITY_ORACLE_TARGET",
        "EOC",
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_SERVICE",
        "FREEPDB1",
    )

    assert job.get_oracle_capacity_target() == "EOC"


def test_get_oracle_capacity_target_falls_back_to_oracle_service(
    monkeypatch,
):
    monkeypatch.delenv(
        "INFRADB_CAPACITY_ORACLE_TARGET",
        raising=False,
    )
    monkeypatch.setenv(
        "INFRADB_ORACLE_SERVICE",
        "FREEPDB1",
    )

    assert job.get_oracle_capacity_target() == "FREEPDB1"


def test_get_oracle_capacity_target_uses_default(monkeypatch):
    monkeypatch.delenv(
        "INFRADB_CAPACITY_ORACLE_TARGET",
        raising=False,
    )
    monkeypatch.delenv(
        "INFRADB_ORACLE_SERVICE",
        raising=False,
    )

    assert (
        job.get_oracle_capacity_target()
        == job.DEFAULT_ORACLE_TARGET
    )


@pytest.mark.asyncio
async def test_collect_oracle_capacity_uses_configured_target(
    monkeypatch,
):
    monkeypatch.setenv(
        "INFRADB_CAPACITY_ORACLE_TARGET",
        "EOC",
    )

    captured = {}

    class FakeCollector:
        def __init__(self):
            captured["collector_created"] = True

        async def collect_tablespace_capacity(
            self,
            database: str,
        ) -> dict:
            captured["database"] = database
            return {
                "status": "success",
                "count": 4,
            }

    monkeypatch.setattr(
        job,
        "OracleCapacityCollector",
        FakeCollector,
    )

    result = await job.collect_oracle_capacity()

    assert captured["collector_created"] is True
    assert captured["database"] == "EOC"
    assert result == {
        "status": "success",
        "count": 4,
    }
