from __future__ import annotations

from backend.app.capacity.service import (
    CapacityForecastService,
)
from backend.app.config.settings import Settings
from backend.app.tools.base import Tool


class CapacityForecastTool(Tool):
    """
    Read-only capacity forecasting tool backed by
    historical capacity measurements.
    """

    name = "capacity_forecast"

    description = (
        "Forecast infrastructure or database capacity "
        "using historical measurements stored by InfraDB Assist."
    )

    permission = "capacity.read"

    read_only = True

    parameters = {
        "target": {
            "type": "string",
            "description": (
                "Target system or database name."
            ),
            "required": True,
        },
        "resource": {
            "type": "string",
            "description": (
                "Exact resource name stored in the capacity "
                "measurement history. For Oracle tablespaces, "
                "use SYSTEM, SYSAUX, USERS, or UNDOTBS1, "
                "not 'SYSTEM tablespace'."
            ),
            "required": True,
        },
        "metric": {
            "type": "string",
            "description": (
                "Capacity metric to forecast. "
                "Use used_mb for storage/size/MB growth. "
                "Use used_percent for utilization/percentage "
                "or threshold questions."
            ),
            "required": True,
            "allowed_values": [
                "used_mb",
                "used_percent",
            ],
        },
        "unit": {
            "type": "string",
            "description": (
                "Measurement unit. "
                "Use MB for used_mb and percent for used_percent."
            ),
            "required": True,
            "allowed_values": [
                "MB",
                "percent",
            ],
        },
        "source": {
            "type": "string",
            "description": (
                "Capacity measurement source, such as oracle."
            ),
            "required": False,
        },
        "environment": {
            "type": "string",
            "description": (
                "Environment containing the historical measurements."
            ),
            "required": False,
        },
        "horizon_days": {
            "type": "integer",
            "description": (
                "Number of days into the future for the forecast."
            ),
            "required": False,
        },
        "threshold": {
            "type": "number",
            "description": (
                "Optional capacity threshold for breach prediction. "
                "Normally used with used_percent."
            ),
            "required": False,
        },
    }

    DEFAULT_SOURCE = "oracle"
    DEFAULT_HORIZON_DAYS = 30

    def __init__(
        self,
        service: CapacityForecastService | None = None,
    ):
        self.service = (
            service
            or CapacityForecastService()
        )

    def build_request(
        self,
        **kwargs,
    ) -> dict:
        """
        Build and validate a capacity forecast request.
        """

        target = kwargs.get("target")

        if not isinstance(target, str):
            raise ValueError(
                "Target must be a string."
            )

        target = target.strip()

        if not target:
            raise ValueError(
                "Target is required."
            )

        resource = kwargs.get("resource")

        if not isinstance(resource, str):
            raise ValueError(
                "Resource must be a string."
            )

        resource = resource.strip()

        if not resource:
            raise ValueError(
                "Resource is required."
            )

        resource = self._normalize_resource(
            resource
        )

        metric = kwargs.get("metric")

        if not isinstance(metric, str):
            raise ValueError(
                "Metric is required."
            )

        metric = metric.strip()

        if metric not in {
            "used_mb",
            "used_percent",
        }:
            raise ValueError(
                "Unsupported capacity metric."
            )

        unit = kwargs.get("unit")

        if not isinstance(unit, str):
            raise ValueError(
                "Unit is required."
            )

        unit = unit.strip()

        unit = self._normalize_unit(
            unit
        )

        self._validate_metric_unit(
            metric=metric,
            unit=unit,
        )

        source = kwargs.get(
            "source",
            self.DEFAULT_SOURCE,
        )

        environment = kwargs.get(
            "environment",
            Settings.environment
            or "development",
        )

        if not isinstance(source, str):
            raise ValueError(
                "Source must be a string."
            )

        if not source.strip():
            raise ValueError(
                "Source must not be empty."
            )

        if not isinstance(environment, str):
            raise ValueError(
                "Environment must be a string."
            )

        if not environment.strip():
            raise ValueError(
                "Environment must not be empty."
            )

        horizon_days = kwargs.get(
            "horizon_days",
            self.DEFAULT_HORIZON_DAYS,
        )

        if isinstance(
            horizon_days,
            bool,
        ) or not isinstance(
            horizon_days,
            int,
        ):
            raise ValueError(
                "Horizon days must be an integer."
            )

        if horizon_days < 1:
            raise ValueError(
                "Horizon days must be greater than zero."
            )

        threshold = kwargs.get(
            "threshold"
        )

        if threshold is not None:
            if isinstance(
                threshold,
                bool,
            ) or not isinstance(
                threshold,
                (int, float),
            ):
                raise ValueError(
                    "Threshold must be numeric."
                )

            if metric != "used_percent":
                raise ValueError(
                    "Threshold forecasting requires used_percent metric."
                )

        return {
            "target": target,
            "resource": resource,
            "metric": metric,
            "unit": unit,
            "source": source.strip(),
            "environment": environment.strip(),
            "horizon_days": horizon_days,
            "threshold": threshold,
        }

    async def execute(
        self,
        request: dict,
    ) -> dict:
        """
        Generate a read-only capacity forecast.
        """

        result = self.service.forecast(
            target=request["target"],
            resource=request["resource"],
            metric=request["metric"],
            unit=request["unit"],
            source=request["source"],
            environment=request["environment"],
            horizon_days=request["horizon_days"],
            threshold=request["threshold"],
        )

        return {
            "tool": self.name,
            **result,
        }

    @staticmethod
    def _normalize_resource(
        resource: str,
    ) -> str:
        """
        Normalize human-friendly resource names into
        the canonical resource stored in PostgreSQL.

        Example:
            "SYSTEM tablespace" -> "SYSTEM"
        """

        normalized = " ".join(
            resource.split()
        )

        lowered = normalized.lower()

        suffixes = (
            " tablespace",
            " table space",
        )

        for suffix in suffixes:
            if lowered.endswith(suffix):
                normalized = normalized[
                    : -len(suffix)
                ].strip()
                break

        return normalized

    @staticmethod
    def _normalize_unit(
        unit: str,
    ) -> str:
        normalized = unit.strip().lower()

        if normalized in {
            "mb",
            "megabyte",
            "megabytes",
        }:
            return "MB"

        if normalized in {
            "%",
            "percent",
            "percentage",
        }:
            return "percent"

        raise ValueError(
            "Unsupported capacity unit."
        )

    @staticmethod
    def _validate_metric_unit(
        metric: str,
        unit: str,
    ) -> None:
        if (
            metric == "used_mb"
            and unit != "MB"
        ):
            raise ValueError(
                "used_mb metric requires MB unit."
            )

        if (
            metric == "used_percent"
            and unit != "percent"
        ):
            raise ValueError(
                "used_percent metric requires percent unit."
            )