from __future__ import annotations

import asyncio

from backend.app.capacity.job import (
    collect_oracle_capacity,
)


class CapacityScheduler:
    """
    Simple asyncio-based scheduler for periodic
    Oracle capacity collection.
    """

    DEFAULT_INTERVAL_SECONDS = 300

    def __init__(
        self,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    ):
        if interval_seconds < 1:
            raise ValueError(
                "Collection interval must be greater than zero."
            )

        self.interval_seconds = interval_seconds

    async def run_once(self) -> dict:
        """
        Execute one collection cycle.
        """
        return await collect_oracle_capacity()

    async def run_forever(self) -> None:
        """
        Continuously collect Oracle capacity data.
        """

        while True:
            try:
                result = await self.run_once()

                print(
                    f"Capacity collection successful: "
                    f"{result['count']} measurements"
                )

            except Exception as exc:
                print(
                    f"Capacity collection failed: {exc}"
                )

            await asyncio.sleep(
                self.interval_seconds
            )
