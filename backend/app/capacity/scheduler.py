import asyncio
import os

from backend.app.capacity.job import collect_oracle_capacity


class CapacityScheduler:
    DEFAULT_INTERVAL_SECONDS = 300

    def __init__(self, interval_seconds: int | None = None):
        self.interval_seconds = (
            interval_seconds
            if interval_seconds is not None
            else self._load_interval_seconds()
        )

        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")

        self.running = False

    @classmethod
    def _load_interval_seconds(cls) -> int:
        raw_value = os.getenv(
            "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS",
            str(cls.DEFAULT_INTERVAL_SECONDS),
        )

        try:
            interval_seconds = int(raw_value)
        except ValueError as exc:
            raise ValueError(
                "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS "
                "must be a valid integer"
            ) from exc

        if interval_seconds <= 0:
            raise ValueError(
                "INFRADB_CAPACITY_COLLECTION_INTERVAL_SECONDS "
                "must be greater than 0"
            )

        return interval_seconds

    async def run(self) -> None:
        self.running = True

        while self.running:
            try:
                result = await collect_oracle_capacity()
                print(
                    "Capacity collection successful: "
                    f"{result.get('count', 0)} measurements"
                )
            except Exception as exc:
                print(f"Capacity collection failed: {exc}")

            if self.running:
                await asyncio.sleep(self.interval_seconds)

    def stop(self) -> None:
        self.running = False