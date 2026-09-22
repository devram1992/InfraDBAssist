import asyncio
import os

from backend.app.capacity.job import collect_capacity


class CapacityScheduler:
    DEFAULT_INTERVAL_SECONDS = 300

    def __init__(
        self,
        interval_seconds: int | None = None,
    ):
        self.interval_seconds = (
            interval_seconds
            if interval_seconds is not None
            else self._load_interval_seconds()
        )

        if self.interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than 0"
            )

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
                result = await collect_capacity()

                status = result.get(
                    "status",
                    "unknown",
                )

                count = result.get(
                    "count",
                    0,
                )

                successful = result.get(
                    "successful_collectors",
                    0,
                )

                failed = result.get(
                    "failed_collectors",
                    0,
                )

                print(
                    "Capacity collection completed: "
                    f"status={status}, "
                    f"measurements={count}, "
                    f"successful_collectors={successful}, "
                    f"failed_collectors={failed}"
                )

                for collection in result.get(
                    "collections",
                    [],
                ):
                    if collection.get("status") == "error":
                        print(
                            "Capacity collection error: "
                            f"source={collection.get('source')}, "
                            f"error={collection.get('error')}"
                        )

            except Exception as exc:
                print(
                    "Capacity collection failed: "
                    f"{exc}"
                )

            if self.running:
                await asyncio.sleep(
                    self.interval_seconds
                )

    def stop(self) -> None:
        self.running = False