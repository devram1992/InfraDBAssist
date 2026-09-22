from __future__ import annotations

from datetime import datetime, timezone

from backend.app.capacity.repository import CapacityRepository
from backend.app.config.settings import Settings
from backend.app.tools.oracle.tool import OracleTool


class OracleCapacityCollector:
    """
    Collect Oracle tablespace capacity metrics and persist them
    into the generic capacity measurement store.
    """

    def __init__(
        self,
        oracle_tool: OracleTool | None = None,
        repository: CapacityRepository | None = None,
    ):
        self.oracle_tool = (
            oracle_tool
            or OracleTool()
        )

        self.repository = (
            repository
            or CapacityRepository()
        )

    async def collect_tablespace_capacity(
        self,
        database: str | None = None,
    ) -> dict:
        """
        Collect current Oracle tablespace utilization.

        Two first-class metrics are stored for every tablespace:
        - used_percent
        - used_mb

        Total/free capacity remain available in metadata.
        """

        request = self.oracle_tool.build_request(
            database=database,
            action="tablespace",
        )

        result = await self.oracle_tool.execute(
            request
        )

        if result.get("status") != "success":
            raise RuntimeError(
                "Oracle tablespace collection failed."
            )

        database_name = result.get(
            "database",
            database
            or Settings.oracle_service
            or "UNKNOWN",
        )

        tablespaces = result.get(
            "tablespaces",
            [],
        )

        observed_at = datetime.now(
            timezone.utc
        )

        environment = (
            Settings.environment
            or "development"
        )

        stored_measurements = []

        for tablespace in tablespaces:
            resource = tablespace.get(
                "tablespace_name",
                "UNKNOWN",
            )

            total_mb = float(
                tablespace.get(
                    "total_mb",
                    0,
                )
                or 0
            )

            used_mb = float(
                tablespace.get(
                    "used_mb",
                    0,
                )
                or 0
            )

            free_mb = float(
                tablespace.get(
                    "free_mb",
                    0,
                )
                or 0
            )

            used_percent = float(
                tablespace.get(
                    "used_percent",
                    0,
                )
                or 0
            )

            metadata = {
                "total_mb": total_mb,
                "free_mb": free_mb,
            }

            used_percent_id = (
                self.repository.record_measurement(
                    observed_at=observed_at,
                    environment=environment,
                    source="oracle",
                    target=database_name,
                    resource=resource,
                    metric="used_percent",
                    value=used_percent,
                    unit="percent",
                    metadata={
                        **metadata,
                        "used_mb": used_mb,
                    },
                )
            )

            used_mb_id = (
                self.repository.record_measurement(
                    observed_at=observed_at,
                    environment=environment,
                    source="oracle",
                    target=database_name,
                    resource=resource,
                    metric="used_mb",
                    value=used_mb,
                    unit="MB",
                    metadata={
                        **metadata,
                        "used_percent": used_percent,
                    },
                )
            )

            stored_measurements.append(
                {
                    "database": database_name,
                    "tablespace": resource,
                    "used_percent": used_percent,
                    "used_mb": used_mb,
                    "free_mb": free_mb,
                    "total_mb": total_mb,
                    "used_percent_measurement_id": (
                        used_percent_id
                    ),
                    "used_mb_measurement_id": (
                        used_mb_id
                    ),
                    "observed_at": observed_at,
                }
            )

        return {
            "status": "success",
            "source": "oracle",
            "database": database_name,
            "metric": "capacity",
            "observed_at": observed_at,
            "count": len(
                stored_measurements
            ),
            "measurements": stored_measurements,
        }