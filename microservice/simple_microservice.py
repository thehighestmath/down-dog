import asyncio
import httpx
import time
from fastapi import FastAPI

api = FastAPI()


@api.get("/")
def read_root():
    return {"message": "Привет, брат! Микросервис работает!"}


# И вот эту
@api.get("/check")
def check_service():
    return {"status": "ok", "service": "microservice"}


async def get_poses_api(category=None, difficulty=None, focus=None):
    url = 'http://localhost:8000/api/poses'

    # собираем параметры в словарь (httpx сам сделает ?category=...&difficulty=...)
    params = {}
    if category is not None:
        params['category'] = category
    if difficulty is not None:
        params['difficulty'] = difficulty
    if focus is not None:
        params['focus'] = focus

    for i in range(6):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

        data = response.json()
        print('count: {}, params: {}'.format(len(data), params))


async def main():
    tasks = [
        asyncio.ensure_future(get_poses_api(category='balancing')),
        asyncio.ensure_future(get_poses_api(difficulty=1)),
        asyncio.ensure_future(get_poses_api(focus='back')),
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time() - start
    print(f'time {end:0.2f} seconds')
    print(f'mean time for 1 request: {end / 18:0.2f} seconds')
