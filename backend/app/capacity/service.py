from __future__ import annotations

from datetime import datetime

from backend.app.capacity.forecaster import (
    CapacityForecaster,
    CapacitySample,
)
from backend.app.capacity.repository import (
    CapacityRepository,
)
from backend.app.config.settings import Settings


class CapacityForecastService:
    """
    Service layer that retrieves historical capacity measurements
    and generates a forecast.
    """

    DEFAULT_HORIZON_DAYS = 30

    # Recommended minimum historical period for an operational
    # capacity forecast. Forecasts are still calculated when the
    # history is shorter, but the result is marked accordingly.
    RECOMMENDED_MINIMUM_HISTORY_DAYS = 7.0

    def __init__(
        self,
        repository: CapacityRepository | None = None,
        forecaster: CapacityForecaster | None = None,
    ):
        self.repository = (
            repository or CapacityRepository()
        )

        self.forecaster = (
            forecaster or CapacityForecaster()
        )

    def forecast(
        self,
        *,
        target: str,
        resource: str,
        metric: str,
        unit: str,
        source: str = "oracle",
        environment: str | None = None,
        horizon_days: int = DEFAULT_HORIZON_DAYS,
        threshold: float | None = None,
    ) -> dict:
        """
        Generate a capacity forecast from stored historical measurements.
        """

        if not target.strip():
            raise ValueError(
                "Target is required."
            )

        if not resource.strip():
            raise ValueError(
                "Resource is required."
            )

        if not metric.strip():
            raise ValueError(
                "Metric is required."
            )

        if not unit.strip():
            raise ValueError(
                "Unit is required."
            )

        environment = (
            environment
            or Settings.environment
            or "development"
        )

        measurements = (
            self.repository.get_measurements(
                environment=environment,
                source=source,
                target=target,
                resource=resource,
                metric=metric,
                unit=unit,
            )
        )

        samples = [
            CapacitySample(
                observed_at=self._get_timestamp(
                    measurement["observed_at"]
                ),
                value=float(
                    measurement["value"]
                ),
            )
            for measurement in measurements
        ]

        data_quality = (
            self._evaluate_data_quality(
                samples
            )
        )

        forecast_result = (
            self.forecaster.forecast(
                samples=samples,
                horizon_days=horizon_days,
                threshold=threshold,
            )
        )

        return {
            "status": "success",
            "environment": environment,
            "source": source,
            "target": target,
            "resource": resource,
            "metric": metric,
            "unit": unit,
            "forecast": forecast_result,
            "data_quality": data_quality,
        }

    def _evaluate_data_quality(
        self,
        samples: list[CapacitySample],
    ) -> dict:
        """
        Evaluate whether the available historical period is
        sufficient for an operational capacity forecast.

        This does not prevent the mathematical forecast from
        being generated.
        """

        if not samples:
            return {
                "status": "insufficient_data",
                "sample_count": 0,
                "history_duration_days": 0.0,
                "recommended_minimum_history_days": (
                    self.RECOMMENDED_MINIMUM_HISTORY_DAYS
                ),
                "message": (
                    "No historical capacity measurements "
                    "are available."
                ),
            }

        ordered_samples = sorted(
            samples,
            key=lambda sample: sample.observed_at,
        )

        first_timestamp = (
            ordered_samples[0].observed_at
        )

        latest_timestamp = (
            ordered_samples[-1].observed_at
        )

        history_duration_days = (
            latest_timestamp - first_timestamp
        ).total_seconds() / 86400.0

        sample_count = len(
            ordered_samples
        )

        if sample_count < 3:
            return {
                "status": "insufficient_data",
                "sample_count": sample_count,
                "history_duration_days": round(
                    history_duration_days,
                    4,
                ),
                "recommended_minimum_history_days": (
                    self.RECOMMENDED_MINIMUM_HISTORY_DAYS
                ),
                "message": (
                    "At least 3 historical samples "
                    "are required for forecasting."
                ),
            }

        if (
            history_duration_days
            < self.RECOMMENDED_MINIMUM_HISTORY_DAYS
        ):
            return {
                "status": "insufficient_history",
                "sample_count": sample_count,
                "history_duration_days": round(
                    history_duration_days,
                    4,
                ),
                "recommended_minimum_history_days": (
                    self.RECOMMENDED_MINIMUM_HISTORY_DAYS
                ),
                "message": (
                    "Forecast calculated, but the historical "
                    "period is shorter than the recommended "
                    "minimum for an operational capacity forecast."
                ),
            }

        return {
            "status": "sufficient_history",
            "sample_count": sample_count,
            "history_duration_days": round(
                history_duration_days,
                4,
            ),
            "recommended_minimum_history_days": (
                self.RECOMMENDED_MINIMUM_HISTORY_DAYS
            ),
            "message": (
                "Historical data covers the recommended "
                "minimum period for capacity forecasting."
            ),
        }

    @staticmethod
    def _get_timestamp(
        value,
    ) -> datetime:
        """
        Normalize repository timestamps into datetime objects.
        """

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            return datetime.fromisoformat(
                value
            )

        raise ValueError(
            "Measurement timestamp must be a datetime or ISO timestamp."
        )