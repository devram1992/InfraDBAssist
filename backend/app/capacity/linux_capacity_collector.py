from __future__ import annotations

from datetime import datetime, timezone

from backend.app.capacity.repository import CapacityRepository
from backend.app.config.settings import Settings
from backend.app.tools.linux.tool import LinuxTool


class LinuxCapacityCollector:
    """
    Collect Linux server disk capacity metrics and persist them
    into the generic capacity measurement store.

    The current LinuxTool exposes server-level disk_usage.
    Filesystem/path-level collection can be added later when
    LinuxTool provides filesystem-specific data.
    """

    def __init__(
        self,
        linux_tool: LinuxTool | None = None,
        repository: CapacityRepository | None = None,
    ):
        self.linux_tool = linux_tool or LinuxTool()
        self.repository = repository or CapacityRepository()

    @staticmethod
    def _parse_percentage(value: object) -> float:
        """
        Convert values such as:
            68
            68.0
            "68"
            "68%"
        into a float percentage.
        """
        if value is None:
            raise ValueError("Disk usage percentage cannot be empty.")

        if isinstance(value, str):
            normalized = value.strip()

            if normalized.endswith("%"):
                normalized = normalized[:-1].strip()

            if not normalized:
                raise ValueError(
                    "Disk usage percentage cannot be empty."
                )

            try:
                percentage = float(normalized)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid disk usage percentage: {value!r}"
                ) from exc
        else:
            try:
                percentage = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid disk usage percentage: {value!r}"
                ) from exc

        if percentage < 0 or percentage > 100:
            raise ValueError(
                f"Disk usage percentage must be between 0 and 100: "
                f"{percentage}"
            )

        return percentage

    async def collect_disk_capacity(
        self,
        server: str | None = None,
    ) -> dict:
        """
        Collect current Linux server disk utilization.

        Current metric:
            - used_percent

        Current resource:
            - disk

        The target is the Linux server hostname.
        """

        request = self.linux_tool.build_request(
            server=server,
        )

        result = await self.linux_tool.execute(request)

        if result.get("status") != "success":
            raise RuntimeError(
                "Linux disk capacity collection failed."
            )

        data = result.get("data") or {}

        server_name = (
            data.get("server")
            or server
            or "UNKNOWN"
        )

        disk_usage = self._parse_percentage(
            data.get("disk_usage")
        )

        observed_at = datetime.now(timezone.utc)

        environment = (
            Settings.environment
            or "development"
        )

        measurement_id = self.repository.record_measurement(
            observed_at=observed_at,
            environment=environment,
            source="linux",
            target=server_name,
            resource="disk",
            metric="used_percent",
            value=disk_usage,
            unit="percent",
            metadata={
                "disk_usage": disk_usage,
            },
        )

        measurement = {
            "server": server_name,
            "resource": "disk",
            "used_percent": disk_usage,
            "measurement_id": measurement_id,
            "observed_at": observed_at,
        }

        return {
            "status": "success",
            "source": "linux",
            "server": server_name,
            "metric": "capacity",
            "observed_at": observed_at,
            "count": 1,
            "measurements": [
                measurement,
            ],
        }
