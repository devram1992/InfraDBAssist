import os

from backend.app.capacity.linux_capacity_collector import (
    LinuxCapacityCollector,
)
from backend.app.capacity.oracle_collector import (
    OracleCapacityCollector,
)


DEFAULT_ORACLE_TARGET = "FREEPDB1"
DEFAULT_LINUX_TARGET = "PROD-SERVER"


def get_oracle_capacity_target() -> str:
    target = os.getenv("INFRADB_CAPACITY_ORACLE_TARGET")

    if not target:
        target = os.getenv("INFRADB_ORACLE_SERVICE")

    if not target:
        target = DEFAULT_ORACLE_TARGET

    target = target.strip()

    if not target:
        raise ValueError(
            "Oracle capacity target cannot be empty"
        )

    return target


def get_linux_capacity_target() -> str:
    target = os.getenv("INFRADB_CAPACITY_LINUX_SERVER")

    if not target:
        target = os.getenv("INFRADB_LINUX_SERVER")

    if not target:
        target = DEFAULT_LINUX_TARGET

    target = target.strip()

    if not target:
        raise ValueError(
            "Linux capacity target cannot be empty"
        )

    return target


async def collect_oracle_capacity() -> dict:
    """
    Collect Oracle tablespace capacity.

    Kept as a dedicated function for backward compatibility
    and direct execution/testing.
    """
    collector = OracleCapacityCollector()

    target = get_oracle_capacity_target()

    return await collector.collect_tablespace_capacity(
        database=target
    )


async def collect_linux_capacity() -> dict:
    """
    Collect Linux server disk capacity.

    Kept as a dedicated function for direct execution/testing.
    """
    collector = LinuxCapacityCollector()

    target = get_linux_capacity_target()

    return await collector.collect_disk_capacity(
        server=target
    )


async def collect_capacity() -> dict:
    """
    Run all enabled capacity collectors.

    A failure in one collector does not prevent the remaining
    collectors from running.
    """
    collections = []
    total_count = 0
    successful_count = 0
    failed_count = 0

    collectors = (
        (
            "oracle",
            collect_oracle_capacity,
        ),
        (
            "linux",
            collect_linux_capacity,
        ),
    )

    for source, collector_function in collectors:
        try:
            result = await collector_function()

            collections.append(
                {
                    "source": source,
                    "status": result.get(
                        "status",
                        "success",
                    ),
                    "result": result,
                }
            )

            total_count += int(
                result.get("count", 0)
                or 0
            )

            successful_count += 1

        except Exception as exc:
            failed_count += 1

            collections.append(
                {
                    "source": source,
                    "status": "error",
                    "error": str(exc),
                }
            )

    if failed_count == 0:
        status = "success"
    elif successful_count == 0:
        status = "error"
    else:
        status = "partial_success"

    return {
        "status": status,
        "count": total_count,
        "successful_collectors": successful_count,
        "failed_collectors": failed_count,
        "collections": collections,
    }