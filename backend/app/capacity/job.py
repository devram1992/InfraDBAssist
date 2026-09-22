import os

from backend.app.capacity.oracle_collector import OracleCapacityCollector


DEFAULT_ORACLE_TARGET = "FREEPDB1"


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


async def collect_oracle_capacity() -> dict:
    collector = OracleCapacityCollector()

    target = get_oracle_capacity_target()

    return await collector.collect_tablespace_capacity(
        database=target
    )