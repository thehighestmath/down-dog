import asyncio
import logging
import os
import time

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Счётчик выполненных запросов (в asyncio один поток — гонок нет)
request_counter = {"total": 0, "ok": 0, "failed": 0}


async def get_poses_api(
    category: str | None = None,
    difficulty: int | None = None,
    focus: str | None = None,
) -> None:
    url = f"{BACKEND_URL}/api/poses"

    params: dict[str, str | int] = {}
    if category is not None:
        params["category"] = category
    if difficulty is not None:
        params["difficulty"] = difficulty
    if focus is not None:
        params["focus"] = focus

    # Один AsyncClient на весь таск — переиспользуем TCP-соединения
    async with httpx.AsyncClient(timeout=10.0) as client:
        for _ in range(6):
            request_counter["total"] += 1
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except (httpx.HTTPError, httpx.ConnectError) as e:
                request_counter["failed"] += 1
                logger.warning(f"request failed: {e}, params: {params}")
                continue

            request_counter["ok"] += 1
            data = response.json()
            logger.info(f"count: {len(data)}, params: {params}")


async def main() -> None:
    tasks = [
        asyncio.ensure_future(get_poses_api(category="balancing")),
        asyncio.ensure_future(get_poses_api(difficulty=1)),
        asyncio.ensure_future(get_poses_api(focus="back")),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    elapsed = time.time() - start

    total = request_counter["total"]
    ok = request_counter["ok"]
    failed = request_counter["failed"]

    logger.info(f"time {elapsed:0.2f} seconds")
    logger.info(f"total requests: {total} (ok={ok}, failed={failed})")
    if total:
        logger.info(f"mean time for 1 request: {elapsed / total:0.3f} seconds")
