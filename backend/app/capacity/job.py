from __future__ import annotations

from backend.app.capacity.oracle_collector import (
    OracleCapacityCollector,
)


async def collect_oracle_capacity() -> dict:
    """
    Run one Oracle capacity collection cycle.
    """

    collector = OracleCapacityCollector()

    return await collector.collect_tablespace_capacity(
        database="FREEPDB1",
    )
