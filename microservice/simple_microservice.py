import asyncio
import logging
import time

import httpx
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = FastAPI()


@api.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Привет, брат! Микросервис работает!"}


@api.get("/check")
def check_service() -> dict[str, str]:
    return {"status": "ok", "service": "microservice"}


async def get_poses_api(
    category: str | None = None,
    difficulty: int | None = None,
    focus: str | None = None,
) -> None:
    url = "http://backend:8000/api/poses"

    params: dict[str, str | int] = {}
    if category is not None:
        params["category"] = category
    if difficulty is not None:
        params["difficulty"] = difficulty
    if focus is not None:
        params["focus"] = focus

    for _ in range(6):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

        data = response.json()
        # Заменили print на logger.info
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
    end = time.time() - start
    logger.info(f"time {end:0.2f} seconds")
    logger.info(f"mean time for 1 request: {end / 18:0.2f} seconds")
