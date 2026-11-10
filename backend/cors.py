import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("app")

# Локальная разработка: Vite dev-сервер (5173) и стенд docker compose (3000).
# Используется, только если CORS_ORIGINS не задана или пуста.
DEFAULT_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def parse_origins(raw: str | None) -> list[str]:
    """CORS_ORIGINS="https://a.com, https://b.com/" -> ["https://a.com", "https://b.com"]."""
    if raw is None or not raw.strip():
        return list(DEFAULT_DEV_ORIGINS)
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


def setup_cors(app: FastAPI, raw: str | None = None) -> None:
    if raw is None:
        raw = os.getenv("CORS_ORIGINS")
    origins = parse_origins(raw)
    if "*" in origins:
        logger.warning("CORS_ORIGINS содержит '*': API открыт для любого сайта")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,  # cookie-аутентификации нет
        allow_methods=["*"],
        allow_headers=["*"],
    )
