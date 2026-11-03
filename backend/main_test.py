from typing import NoReturn
from unittest.mock import MagicMock

import main
import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

client = TestClient(main.app)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, ["*"]),
        ("", ["*"]),
        ("   ", ["*"]),
        ("https://app.example", ["https://app.example"]),
        (
            "https://app.example, https://admin.example",
            ["https://app.example", "https://admin.example"],
        ),
    ],
)
def test_parse_cors_origins(raw: str | None, expected: list[str]) -> None:
    assert main.parse_cors_origins(raw) == expected


def test_cors_allows_configured_origin_and_rejects_foreign() -> None:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=main.parse_cors_origins(
            "https://app.example,https://admin.example"
        ),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/probe")
    def probe() -> dict[str, bool]:
        return {"ok": True}

    c = TestClient(app)
    allowed = c.get("/probe", headers={"Origin": "https://app.example"})
    assert allowed.headers.get("access-control-allow-origin") == "https://app.example"

    foreign = c.get("/probe", headers={"Origin": "https://evil.example"})
    assert foreign.headers.get("access-control-allow-origin") != "https://evil.example"


def test_health_returns_ok_and_closes_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = MagicMock()

    def connect() -> MagicMock:
        return connection

    monkeypatch.setattr(main, "get_db_connection", connect)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.assert_called_once_with("SELECT 1")
    connection.close.assert_called_once_with()


def test_health_returns_503_when_database_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def connect() -> NoReturn:
        raise RuntimeError("connection refused")

    monkeypatch.setattr(main, "get_db_connection", connect)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable"}
