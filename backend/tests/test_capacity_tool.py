from unittest.mock import MagicMock

import pytest

from backend.app.tools.capacity.tool import (
    CapacityForecastTool,
)


def test_build_request_for_percentage_forecast():
    tool = CapacityForecastTool()

    request = tool.build_request(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="percent",
    )

    assert request == {
        "target": "FREEPDB1",
        "resource": "SYSTEM",
        "metric": "used_percent",
        "unit": "percent",
        "source": "oracle",
        "environment": "development",
        "horizon_days": 30,
        "threshold": None,
    }


def test_build_request_for_storage_forecast():
    tool = CapacityForecastTool()

    request = tool.build_request(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_mb",
        unit="MB",
    )

    assert request == {
        "target": "FREEPDB1",
        "resource": "SYSTEM",
        "metric": "used_mb",
        "unit": "MB",
        "source": "oracle",
        "environment": "development",
        "horizon_days": 30,
        "threshold": None,
    }


def test_build_request_normalizes_tablespace_name():
    tool = CapacityForecastTool()

    request = tool.build_request(
        target="FREEPDB1",
        resource="SYSTEM tablespace",
        metric="used_mb",
        unit="MB",
    )

    assert request["resource"] == "SYSTEM"


def test_build_request_normalizes_unit():
    tool = CapacityForecastTool()

    request = tool.build_request(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_percent",
        unit="%",
    )

    assert request["unit"] == "percent"


def test_build_request_requires_metric():
    tool = CapacityForecastTool()

    with pytest.raises(
        ValueError,
        match="Metric is required",
    ):
        tool.build_request(
            target="FREEPDB1",
            resource="SYSTEM",
            unit="MB",
        )


def test_build_request_requires_unit():
    tool = CapacityForecastTool()

    with pytest.raises(
        ValueError,
        match="Unit is required",
    ):
        tool.build_request(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_mb",
        )


def test_build_request_rejects_invalid_metric():
    tool = CapacityForecastTool()

    with pytest.raises(
        ValueError,
        match="Unsupported capacity metric",
    ):
        tool.build_request(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="free_mb",
            unit="MB",
        )


def test_build_request_rejects_mismatched_unit():
    tool = CapacityForecastTool()

    with pytest.raises(
        ValueError,
        match="used_mb metric requires MB unit",
    ):
        tool.build_request(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_mb",
            unit="percent",
        )


def test_build_request_rejects_threshold_for_mb():
    tool = CapacityForecastTool()

    with pytest.raises(
        ValueError,
        match="Threshold forecasting requires used_percent metric",
    ):
        tool.build_request(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_mb",
            unit="MB",
            threshold=300,
        )


def test_build_request_rejects_invalid_horizon():
    tool = CapacityForecastTool()

    with pytest.raises(
        ValueError,
        match="Horizon days must be greater than zero",
    ):
        tool.build_request(
            target="FREEPDB1",
            resource="SYSTEM",
            metric="used_mb",
            unit="MB",
            horizon_days=0,
        )


@pytest.mark.asyncio
async def test_execute_calls_forecast_service():
    service = MagicMock()

    service.forecast.return_value = {
        "status": "success",
        "environment": "development",
        "source": "oracle",
        "target": "FREEPDB1",
        "resource": "SYSTEM",
        "metric": "used_mb",
        "unit": "MB",
        "forecast": {
            "sample_count": 3,
            "current_value": 295.56,
            "trend": "flat",
            "growth_per_day": 0.0,
            "horizon_days": 30,
            "projected_value": 295.56,
        },
    }

    tool = CapacityForecastTool(
        service=service,
    )

    request = tool.build_request(
        target="FREEPDB1",
        resource="SYSTEM tablespace",
        metric="used_mb",
        unit="MB",
    )

    result = await tool.execute(
        request
    )

    assert result["tool"] == "capacity_forecast"
    assert result["status"] == "success"
    assert result["target"] == "FREEPDB1"
    assert result["resource"] == "SYSTEM"
    assert result["metric"] == "used_mb"

    service.forecast.assert_called_once_with(
        target="FREEPDB1",
        resource="SYSTEM",
        metric="used_mb",
        unit="MB",
        source="oracle",
        environment="development",
        horizon_days=30,
        threshold=None,
    )