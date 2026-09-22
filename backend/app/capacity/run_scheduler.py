from __future__ import annotations

import asyncio

from backend.app.capacity.scheduler import (
    CapacityScheduler,
)


async def main() -> None:
    scheduler = CapacityScheduler(
        interval_seconds=300,
    )

    await scheduler.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(
            "Capacity scheduler stopped."
        )
