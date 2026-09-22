from datetime import datetime, timedelta

import pytest

from backend.app.capacity.forecaster import (
    CapacityForecaster,
    CapacitySample,
)


def create_samples(
    values,
    start=None,
):
    start = start or datetime(
        2026,
        9,
        1,
        10,
        0,
        0,
    )

    return [
        CapacitySample(
            observed_at=(
                start
                + timedelta(days=index)
            ),
            value=value,
        )
        for index, value in enumerate(values)
    ]


def test_forecast_requires_minimum_samples():
    forecaster = CapacityForecaster()

    samples = create_samples(
        [90.0, 91.0]
    )

    with pytest.raises(
        ValueError,
        match="At least 3 historical samples are required",
    ):
        forecaster.forecast(
            samples=samples
        )


def test_forecast_rejects_invalid_horizon():
    forecaster = CapacityForecaster()

    samples = create_samples(
        [90.0, 91.0, 92.0]
    )

    with pytest.raises(
        ValueError,
        match="Forecast horizon must be greater than zero",
    ):
        forecaster.forecast(
            samples=samples,
            horizon_days=0,
        )


def test_forecast_detects_increasing_trend():
    forecaster = CapacityForecaster()

    samples = create_samples(
        [90.0, 91.0, 92.0]
    )

    result = forecaster.forecast(
        samples=samples,
        horizon_days=30,
    )

    assert result["status"] == "success"
    assert result["sample_count"] == 3
    assert result["current_value"] == 92.0
    assert result["trend"] == "increasing"
    assert result["growth_per_day"] == 1.0
    assert result["horizon_days"] == 30
    assert result["projected_value"] == 122.0
    assert result["r_squared"] == 1.0


def test_forecast_predicts_threshold_breach():
    forecaster = CapacityForecaster()

    samples = create_samples(
        [90.0, 91.0, 92.0]
    )

    result = forecaster.forecast(
        samples=samples,
        horizon_days=30,
        threshold=99,
    )

    threshold = result["threshold"]

    assert threshold["configured"] is True
    assert threshold["threshold"] == 99.0
    assert threshold["status"] == (
        "breach_predicted"
    )
    assert threshold["days_until_breach"] == 7.0

    assert (
        threshold["estimated_breach_at"]
        == datetime(
            2026,
            9,
            10,
            10,
            0,
            0,
        )
    )


def test_forecast_detects_already_breached_threshold():
    forecaster = CapacityForecaster()

    samples = create_samples(
        [90.0, 91.0, 92.0]
    )

    latest_timestamp = (
        samples[-1].observed_at
    )

    result = forecaster.forecast(
        samples=samples,
        horizon_days=30,
        threshold=91,
    )

    threshold = result["threshold"]

    assert threshold["configured"] is True
    assert threshold["threshold"] == 91.0
    assert threshold["status"] == (
        "already_breached"
    )

    assert (
        threshold["estimated_breach_at"]
        == latest_timestamp
    )


def test_forecast_detects_decreasing_trend():
    forecaster = CapacityForecaster()

    samples = create_samples(
        [92.0, 91.0, 90.0]
    )

    result = forecaster.forecast(
        samples=samples,
        horizon_days=30,
    )

    assert result["status"] == "success"
    assert result["current_value"] == 90.0
    assert result["trend"] == "decreasing"
    assert result["growth_per_day"] == -1.0
    assert result["projected_value"] == 60.0
    assert result["r_squared"] == 1.0


def test_forecast_detects_flat_trend():
    forecaster = CapacityForecaster()

    samples = create_samples(
        [98.52, 98.52, 98.52]
    )

    result = forecaster.forecast(
        samples=samples,
        horizon_days=30,
        threshold=99,
    )

    assert result["status"] == "success"
    assert result["current_value"] == 98.52
    assert result["trend"] == "flat"
    assert result["growth_per_day"] == 0.0
    assert result["projected_value"] == 98.52
    assert result["r_squared"] == 1.0

    threshold = result["threshold"]

    assert threshold["configured"] is True
    assert threshold["threshold"] == 99.0
    assert threshold["status"] == (
        "no_breach_predicted"
    )
    assert threshold["estimated_breach_at"] is None


def test_forecast_handles_unsorted_samples():
    forecaster = CapacityForecaster()

    start = datetime(
        2026,
        9,
        1,
        10,
        0,
        0,
    )

    samples = [
        CapacitySample(
            observed_at=(
                start
                + timedelta(days=2)
            ),
            value=92.0,
        ),
        CapacitySample(
            observed_at=start,
            value=90.0,
        ),
        CapacitySample(
            observed_at=(
                start
                + timedelta(days=1)
            ),
            value=91.0,
        ),
    ]

    result = forecaster.forecast(
        samples=samples,
        horizon_days=30,
    )

    assert result["status"] == "success"
    assert result["sample_count"] == 3
    assert result["current_value"] == 92.0
    assert result["current_timestamp"] == (
        start
        + timedelta(days=2)
    )
    assert result["trend"] == "increasing"
    assert result["growth_per_day"] == 1.0
    assert result["projected_value"] == 122.0


def test_forecast_rejects_duplicate_timestamps():
    forecaster = CapacityForecaster()

    timestamp = datetime(
        2026,
        9,
        1,
        10,
        0,
        0,
    )

    samples = [
        CapacitySample(
            observed_at=timestamp,
            value=90.0,
        ),
        CapacitySample(
            observed_at=timestamp,
            value=91.0,
        ),
        CapacitySample(
            observed_at=timestamp,
            value=92.0,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="Capacity samples must have different timestamps",
    ):
        forecaster.forecast(
            samples=samples
        )