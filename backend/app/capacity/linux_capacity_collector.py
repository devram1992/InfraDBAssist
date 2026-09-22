from __future__ import annotations

from datetime import datetime, timezone

from backend.app.capacity.repository import CapacityRepository
from backend.app.config.settings import Settings
from backend.app.tools.linux.tool import LinuxTool


class LinuxCapacityCollector:
    """
    Collect Linux filesystem capacity metrics and persist them
    into the generic capacity measurement store.

    Each filesystem/mount point is stored as an independent
    capacity resource.

    First-class metrics:
        - used_percent
        - used_mb

    Additional capacity information is stored in metadata.
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
            raise ValueError(
                "Disk usage percentage cannot be empty."
            )

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
                "Disk usage percentage must be between 0 and 100: "
                f"{percentage}"
            )

        return percentage

    @staticmethod
    def _parse_number(
        value: object,
        field_name: str,
    ) -> float:
        """
        Convert a numeric value into float.
        """
        if value is None:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid {field_name}: {value!r}"
            ) from exc

        if number < 0:
            raise ValueError(
                f"{field_name} cannot be negative: {number}"
            )

        return number

    async def collect_disk_capacity(
        self,
        server: str | None = None,
    ) -> dict:
        """
        Collect current Linux filesystem utilization.

        Each filesystem is persisted independently.

        Example resources:

            /
            /data
            /u01

        For every filesystem the collector stores:

            used_percent
            used_mb
        """
        request = self.linux_tool.build_request(
            server=server,
        )

        result = await self.linux_tool.execute(
            request
        )

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

        environment = (
            Settings.environment
            or "development"
        )

        observed_at = datetime.now(
            timezone.utc
        )

        # Keep the distinction between:
        #
        #   filesystems field missing
        #       -> legacy response; use disk_usage
        #
        #   filesystems field present but empty
        #       -> explicit empty filesystem response; fail
        #
        #   filesystems field populated
        #       -> filesystem-aware collection
        filesystem_payload = data.get(
            "filesystems"
        )

        stored_measurements = []

        if filesystem_payload is not None:
            if not isinstance(
                filesystem_payload,
                list,
            ):
                raise ValueError(
                    "Linux filesystem data must be a list."
                )

            if not filesystem_payload:
                raise RuntimeError(
                    "Linux disk capacity collection returned "
                    "no filesystem measurements."
                )

            for filesystem in filesystem_payload:
                if not isinstance(
                    filesystem,
                    dict,
                ):
                    raise ValueError(
                        "Linux filesystem entry must be a dictionary."
                    )

                resource = (
                    filesystem.get(
                        "mount_point"
                    )
                    or "UNKNOWN"
                )

                total_mb = self._parse_number(
                    filesystem.get(
                        "total_mb",
                        0,
                    ),
                    "total_mb",
                )

                used_mb = self._parse_number(
                    filesystem.get(
                        "used_mb",
                        0,
                    ),
                    "used_mb",
                )

                available_mb = self._parse_number(
                    filesystem.get(
                        "available_mb",
                        0,
                    ),
                    "available_mb",
                )

                used_percent = self._parse_percentage(
                    filesystem.get(
                        "used_percent"
                    )
                )

                metadata = {
                    "filesystem": filesystem.get(
                        "filesystem"
                    ),
                    "total_mb": total_mb,
                    "available_mb": available_mb,
                    "used_mb": used_mb,
                    "used_percent": used_percent,
                }

                used_percent_id = (
                    self.repository.record_measurement(
                        observed_at=observed_at,
                        environment=environment,
                        source="linux",
                        target=server_name,
                        resource=resource,
                        metric="used_percent",
                        value=used_percent,
                        unit="percent",
                        metadata=metadata,
                    )
                )

                used_mb_id = (
                    self.repository.record_measurement(
                        observed_at=observed_at,
                        environment=environment,
                        source="linux",
                        target=server_name,
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
                        "server": server_name,
                        "resource": resource,
                        "filesystem": filesystem.get(
                            "filesystem"
                        ),
                        "used_percent": used_percent,
                        "used_mb": used_mb,
                        "total_mb": total_mb,
                        "available_mb": available_mb,
                        "used_percent_measurement_id": (
                            used_percent_id
                        ),
                        "used_mb_measurement_id": (
                            used_mb_id
                        ),
                        "observed_at": observed_at,
                    }
                )

        else:
            # Backward-compatible path for older LinuxTool
            # responses that do not contain a filesystems field.
            disk_usage = self._parse_percentage(
                data.get("disk_usage")
            )

            measurement_id = (
                self.repository.record_measurement(
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
            )

            stored_measurements.append(
                {
                    "server": server_name,
                    "resource": "disk",
                    "used_percent": disk_usage,
                    "measurement_id": measurement_id,
                    "observed_at": observed_at,
                }
            )

        if not stored_measurements:
            raise RuntimeError(
                "Linux disk capacity collection returned "
                "no filesystem measurements."
            )

        return {
            "status": "success",
            "source": "linux",
            "server": server_name,
            "metric": "capacity",
            "observed_at": observed_at,
            "count": len(
                stored_measurements
            ),
            "measurements": stored_measurements,
        }
