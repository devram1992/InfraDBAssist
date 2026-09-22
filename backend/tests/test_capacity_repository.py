from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from backend.app.capacity.repository import (
    CapacityRepository,
)


@pytest.fixture
def repository(monkeypatch):
    repository = CapacityRepository()

    connection = MagicMock()
    cursor = MagicMock()

    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor

    monkeypatch.setattr(
        "backend.app.capacity.repository.get_connection",
        lambda: connection,
    )

    return (
        repository,
        connection,
        cursor,
    )


def test_record_measurement(
    repository,
):
    repo, connection, cursor = repository

    cursor.fetchone.return_value = [101]

    observed_at = datetime(
        2026,
        9,
        22,
        10,
        0,
        tzinfo=timezone.utc,
    )

    result = repo.record_measurement(
        observed_at=observed_at,
        environment="development",
        source="oracle",
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        value=98.52,
        unit="percent",
        metadata={
            "tablespace": "SYSTEM",
        },
    )

    assert result == 101

    cursor.execute.assert_called_once()
    connection.commit.assert_called_once()


def test_record_measurement_rejects_empty_environment(
    repository,
):
    repo, _, _ = repository

    with pytest.raises(
        ValueError,
        match="Environment cannot be empty",
    ):
        repo.record_measurement(
            observed_at=datetime.now(
                timezone.utc
            ),
            environment="",
            source="oracle",
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_percent",
            value=90,
            unit="percent",
        )


def test_record_measurement_rejects_empty_source(
    repository,
):
    repo, _, _ = repository

    with pytest.raises(
        ValueError,
        match="Source cannot be empty",
    ):
        repo.record_measurement(
            observed_at=datetime.now(
                timezone.utc
            ),
            environment="development",
            source="",
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_percent",
            value=90,
            unit="percent",
        )


def test_record_measurement_rejects_non_numeric_value(
    repository,
):
    repo, _, _ = repository

    with pytest.raises(
        ValueError,
        match="Measurement value must be numeric",
    ):
        repo.record_measurement(
            observed_at=datetime.now(
                timezone.utc
            ),
            environment="development",
            source="oracle",
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_percent",
            value="90",
            unit="percent",
        )


def test_get_measurements(
    repository,
):
    repo, _, cursor = repository

    observed_at = datetime(
        2026,
        9,
        22,
        10,
        0,
        tzinfo=timezone.utc,
    )

    cursor.fetchall.return_value = [
        (
            101,
            observed_at,
            "development",
            "oracle",
            "FREEPDB1",
            "SYSTEM",
            "used_percent",
            98.52,
            "percent",
            {
                "tablespace": "SYSTEM",
            },
            observed_at,
        )
    ]

    result = repo.get_measurements(
        environment="development",
        source="oracle",
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
    )

    assert len(result) == 1
    assert result[0]["id"] == 101
    assert result[0]["value"] == 98.52
    assert result[0]["unit"] == "percent"
    assert result[0]["resource"] == "SYSTEM"

    cursor.execute.assert_called_once()


def test_get_measurements_rejects_invalid_limit(
    repository,
):
    repo, _, _ = repository

    with pytest.raises(
        ValueError,
        match="Limit must be greater than zero",
    ):
        repo.get_measurements(
            environment="development",
            source="oracle",
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_percent",
            limit=0,
        )


def test_get_latest_measurement_returns_latest(
    repository,
):
    repo, _, cursor = repository

    observed_at = datetime(
        2026,
        9,
        22,
        12,
        0,
        tzinfo=timezone.utc,
    )

    cursor.fetchone.return_value = (
        102,
        observed_at,
        "development",
        "oracle",
        "FREEPDB1",
        "SYSTEM",
        "used_percent",
        99.10,
        "percent",
        {},
        observed_at,
    )

    result = repo.get_latest_measurement(
        environment="development",
        source="oracle",
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
    )

    assert result is not None
    assert result["id"] == 102
    assert result["value"] == 99.10


def test_get_latest_measurement_returns_none_when_empty(
    repository,
):
    repo, _, cursor = repository

    cursor.fetchone.return_value = None

    result = repo.get_latest_measurement(
        environment="development",
        source="oracle",
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
    )

    assert result is None


def test_count_measurements(
    repository,
):
    repo, _, cursor = repository

    cursor.fetchone.return_value = [15]

    result = repo.count_measurements(
        environment="development",
        source="oracle",
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
    )

    assert result == 15
