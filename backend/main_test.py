from typing import NoReturn
from unittest.mock import MagicMock

import main
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)


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


def test_load_poses_from_db_filters_only_poses_with_images(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    def connect() -> MagicMock:
        return connection

    monkeypatch.setattr(main, "get_db_connection", connect)

    poses = main.load_poses_from_db()

    assert poses == []
    cursor.execute.assert_called_once_with(
        "SELECT id, name_ru, name_sanskrit, name_en, category, "
        "difficulty, focus_areas, contraindications, description, "
        "image_url, audio_url, hold_time_sec, full_cycle_sec "
        "FROM poses "
        "WHERE image_url IS NOT NULL AND image_url != '' "
        "ORDER BY id"
    )
    connection.close.assert_called_once_with()
