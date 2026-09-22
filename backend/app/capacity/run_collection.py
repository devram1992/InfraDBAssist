from __future__ import annotations

import asyncio
import json

from backend.app.capacity.job import (
    collect_oracle_capacity,
)


async def main() -> None:
    result = await collect_oracle_capacity()

    print(
        json.dumps(
            result,
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
