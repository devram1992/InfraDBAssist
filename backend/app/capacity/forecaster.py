from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class CapacitySample:
    """
    Historical capacity measurement.
    """

    observed_at: datetime
    value: float


class CapacityForecaster:
    """
    Forecast future capacity using a simple linear trend.

    The engine is intentionally independent of Oracle, Grafana,
    PostgreSQL, or any other monitoring source.

    It accepts historical measurements and returns:
        - current value
        - trend direction
        - growth rate
        - projected future value
        - threshold breach information
        - regression fit quality
    """

    DEFAULT_MINIMUM_SAMPLES = 3

    def __init__(
        self,
        minimum_samples: int = DEFAULT_MINIMUM_SAMPLES,
    ):
        if minimum_samples < 2:
            raise ValueError(
                "Minimum sample count must be at least 2."
            )

        self.minimum_samples = minimum_samples

    def forecast(
        self,
        samples: list[CapacitySample],
        horizon_days: int = 30,
        threshold: float | None = None,
    ) -> dict:
        """
        Generate a capacity forecast from historical samples.

        Args:
            samples:
                Historical measurements.

            horizon_days:
                Number of days into the future to project.

            threshold:
                Optional threshold for estimating when it will
                be reached.

        Returns:
            Forecast result dictionary.
        """

        self._validate_samples(samples)

        if horizon_days < 1:
            raise ValueError(
                "Forecast horizon must be greater than zero."
            )

        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                raise ValueError(
                    "Threshold must be numeric."
                )

        ordered_samples = sorted(
            samples,
            key=lambda sample: sample.observed_at,
        )

        first_timestamp = ordered_samples[0].observed_at
        latest_sample = ordered_samples[-1]

        x_values = [
            (
                sample.observed_at - first_timestamp
            ).total_seconds()
            / 86400.0
            for sample in ordered_samples
        ]

        y_values = [
            float(sample.value)
            for sample in ordered_samples
        ]

        slope, intercept = self._linear_regression(
            x_values,
            y_values,
        )

        latest_x = x_values[-1]

        future_x = latest_x + horizon_days

        projected_value = (
            intercept
            + slope * future_x
        )

        current_value = float(
            latest_sample.value
        )

        growth_per_day = slope

        if abs(growth_per_day) < 1e-9:
            trend = "flat"
        elif growth_per_day > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        r_squared = self._calculate_r_squared(
            x_values,
            y_values,
            slope,
            intercept,
        )

        forecast_at = (
            latest_sample.observed_at
            + timedelta(
                days=horizon_days
            )
        )

        threshold_result = (
            self._calculate_threshold_breach(
                samples=ordered_samples,
                slope=slope,
                intercept=intercept,
                threshold=float(threshold),
            )
            if threshold is not None
            else {
                "configured": False,
            }
        )

        return {
            "status": "success",
            "sample_count": len(ordered_samples),
            "current_value": current_value,
            "current_timestamp": (
                latest_sample.observed_at
            ),
            "trend": trend,
            "growth_per_day": round(
                growth_per_day,
                6,
            ),
            "horizon_days": horizon_days,
            "forecast_at": forecast_at,
            "projected_value": round(
                projected_value,
                6,
            ),
            "r_squared": round(
                r_squared,
                6,
            ),
            "threshold": threshold_result,
        }

    def _validate_samples(
        self,
        samples: list[CapacitySample],
    ) -> None:
        if not samples:
            raise ValueError(
                "At least one capacity sample is required."
            )

        if len(samples) < self.minimum_samples:
            raise ValueError(
                f"At least {self.minimum_samples} "
                "historical samples are required "
                "for forecasting."
            )

        for sample in samples:
            if not isinstance(
                sample.observed_at,
                datetime,
            ):
                raise ValueError(
                    "Sample timestamp must be a datetime."
                )

            if not isinstance(
                sample.value,
                (int, float),
            ):
                raise ValueError(
                    "Sample value must be numeric."
                )

    def _linear_regression(
        self,
        x_values: list[float],
        y_values: list[float],
    ) -> tuple[float, float]:
        """
        Calculate least-squares linear regression.

        Returns:
            slope, intercept
        """

        count = len(x_values)

        mean_x = (
            sum(x_values) / count
        )

        mean_y = (
            sum(y_values) / count
        )

        numerator = sum(
            (
                (x - mean_x)
                * (y - mean_y)
            )
            for x, y in zip(
                x_values,
                y_values,
            )
        )

        denominator = sum(
            (
                x - mean_x
            ) ** 2
            for x in x_values
        )

        if denominator == 0:
            raise ValueError(
                "Capacity samples must have different timestamps."
            )

        slope = (
            numerator
            / denominator
        )

        intercept = (
            mean_y
            - slope * mean_x
        )

        return slope, intercept

    def _calculate_r_squared(
        self,
        x_values: list[float],
        y_values: list[float],
        slope: float,
        intercept: float,
    ) -> float:
        """
        Calculate the coefficient of determination.
        """

        mean_y = (
            sum(y_values)
            / len(y_values)
        )

        total_sum_squares = sum(
            (
                y - mean_y
            ) ** 2
            for y in y_values
        )

        if total_sum_squares == 0:
            return 1.0

        residual_sum_squares = sum(
            (
                y
                - (
                    intercept
                    + slope * x
                )
            ) ** 2
            for x, y in zip(
                x_values,
                y_values,
            )
        )

        return max(
            0.0,
            min(
                1.0,
                1
                - (
                    residual_sum_squares
                    / total_sum_squares
                ),
            ),
        )

    def _calculate_threshold_breach(
        self,
        samples: list[CapacitySample],
        slope: float,
        intercept: float,
        threshold: float,
    ) -> dict:
        """
        Estimate when a rising trend reaches the threshold.
        """

        latest_sample = samples[-1]

        current_value = float(
            latest_sample.value
        )

        if current_value >= threshold:
            return {
                "configured": True,
                "threshold": threshold,
                "status": "already_breached",
                "estimated_breach_at": (
                    latest_sample.observed_at
                ),
            }

        if slope <= 0:
            return {
                "configured": True,
                "threshold": threshold,
                "status": "no_breach_predicted",
                "estimated_breach_at": None,
            }

        first_timestamp = samples[0].observed_at

        latest_x = (
            latest_sample.observed_at
            - first_timestamp
        ).total_seconds() / 86400.0

        threshold_x = (
            threshold - intercept
        ) / slope

        days_from_latest = (
            threshold_x - latest_x
        )

        if days_from_latest <= 0:
            return {
                "configured": True,
                "threshold": threshold,
                "status": "already_breached",
                "estimated_breach_at": (
                    latest_sample.observed_at
                ),
            }

        breach_at = (
            latest_sample.observed_at
            + timedelta(
                days=days_from_latest
            )
        )

        return {
            "configured": True,
            "threshold": threshold,
            "status": "breach_predicted",
            "days_until_breach": round(
                days_from_latest,
                2,
            ),
            "estimated_breach_at": breach_at,
        }
