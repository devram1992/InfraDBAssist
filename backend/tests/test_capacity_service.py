from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from backend.app.capacity.service import (
    CapacityForecastService,
)


class FakeCapacityRepository:
    def __init__(
        self,
        measurements=None,
    ):
        self.measurements = (
            measurements or []
        )
        self.calls = []

    def get_measurements(
        self,
        *,
        environment,
        source,
        target,
        resource,
        metric,
        unit=None,
        start=None,
        end=None,
        limit=None,
    ):
        self.calls.append(
            {
                "environment": environment,
                "source": source,
                "target": target,
                "resource": resource,
                "metric": metric,
                "unit": unit,
                "start": start,
                "end": end,
                "limit": limit,
            }
        )

        return self.measurements


def create_measurements():
    start = datetime(
        2026,
        9,
        19,
        10,
        0,
        0,
    )

    return [
        {
            "observed_at": start,
            "value": Decimal("90.0"),
        },
        {
            "observed_at": (
                start
                + timedelta(days=1)
            ),
            "value": Decimal("91.0"),
        },
        {
            "observed_at": (
                start
                + timedelta(days=2)
            ),
            "value": Decimal("92.0"),
        },
    ]


def test_forecast_capacity():
    repository = (
        FakeCapacityRepository(
            create_measurements()
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    result = service.forecast(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
    )

    assert result["status"] == "success"
    assert result["environment"] == "development"
    assert result["source"] == "oracle"
    assert result["target"] == "FREEPDB1"
    assert result["resource"] == "SYSTEM"
    assert result["metric"] == "used_percent"
    assert result["unit"] == "percent"

    forecast = result["forecast"]

    assert forecast["sample_count"] == 3
    assert forecast["current_value"] == 92.0
    assert forecast["trend"] == "increasing"
    assert forecast["growth_per_day"] == 1.0
    assert forecast["projected_value"] == 122.0


def test_forecast_passes_repository_filters():
    repository = (
        FakeCapacityRepository(
            create_measurements()
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    service.forecast(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
        source="oracle",
        environment="development",
        horizon_days=15,
        threshold=99,
    )

    assert len(
        repository.calls
    ) == 1

    call = repository.calls[0]

    assert call["environment"] == "development"
    assert call["source"] == "oracle"
    assert call["target"] == "FREEPDB1"
    assert call["resource"] == "SYSTEM"
    assert call["metric"] == "used_percent"
    assert call["unit"] == "percent"


def test_forecast_supports_threshold():
    repository = (
        FakeCapacityRepository(
            create_measurements()
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    result = service.forecast(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
        threshold=99,
    )

    threshold = (
        result["forecast"]["threshold"]
    )

    assert threshold["configured"] is True
    assert threshold["threshold"] == 99.0
    assert threshold["status"] == "breach_predicted"
    assert (
        threshold["days_until_breach"]
        == 7.0
    )


def test_forecast_requires_target():
    repository = (
        FakeCapacityRepository(
            create_measurements()
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    with pytest.raises(
        ValueError,
        match="Target is required",
    ):
        service.forecast(
            target="",
            resource="SYSTEM",
            metric="used_percent",
            unit="percent",
        )


def test_forecast_requires_resource():
    repository = (
        FakeCapacityRepository(
            create_measurements()
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    with pytest.raises(
        ValueError,
        match="Resource is required",
    ):
        service.forecast(
            target="FREEPDB1",
            resource="",
            metric="used_percent",
            unit="percent",
        )


def test_forecast_requires_metric():
    repository = (
        FakeCapacityRepository(
            create_measurements()
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    with pytest.raises(
        ValueError,
        match="Metric is required",
    ):
        service.forecast(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="",
            unit="percent",
        )


def test_forecast_requires_unit():
    repository = (
        FakeCapacityRepository(
            create_measurements()
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    with pytest.raises(
        ValueError,
        match="Unit is required",
    ):
        service.forecast(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_percent",
            unit="",
        )


def test_forecast_fails_with_insufficient_history():
    measurements = [
        {
            "observed_at": datetime(
                2026,
                9,
                22,
                10,
                0,
                0,
            ),
            "value": Decimal("98.52"),
        }
    ]

    repository = (
        FakeCapacityRepository(
            measurements
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    with pytest.raises(
        ValueError,
        match="historical samples are required",
    ):
        service.forecast(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_percent",
            unit="percent",
        )


def test_forecast_accepts_string_timestamp():
    start = "2026-09-19T10:00:00"

    measurements = [
        {
            "observed_at": start,
            "value": Decimal("90"),
        },
        {
            "observed_at": "2026-09-20T10:00:00",
            "value": Decimal("91"),
        },
        {
            "observed_at": "2026-09-21T10:00:00",
            "value": Decimal("92"),
        },
    ]

    repository = (
        FakeCapacityRepository(
            measurements
        )
    )

    service = (
        CapacityForecastService(
            repository=repository
        )
    )

    result = service.forecast(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
    )

    assert (
        result["forecast"]["sample_count"]
        == 3
    )
