from collections.abc import Iterator

import pytest
import storage
from fastapi.testclient import TestClient
from main import app

# storage.get_audio подменяется в каждом тесте, MinIO для тестов не нужен
client = TestClient(app)


def test_audio_is_streamed_with_length(monkeypatch: pytest.MonkeyPatch) -> None:
    requested: list[str] = []

    def fake_get_audio(key: str) -> tuple[Iterator[bytes], int]:
        requested.append(key)
        return iter([b"ID3", b"data"]), 7

    monkeypatch.setattr(storage, "get_audio", fake_get_audio)

    r = client.get("/api/audio/ru/poses/tree")

    assert r.status_code == 200
    assert r.content == b"ID3data"
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.headers["content-length"] == "7"
    assert requested == ["audio/poses_ru/tree.mp3"]


def test_missing_audio_is_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "get_audio", lambda key: None)

    r = client.get("/api/audio/en/phrases/nope")

    assert r.status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/api/audio/de/poses/tree",  # неизвестный язык
        "/api/audio/ru/music/tree",  # неизвестный тип
        "/api/audio/ru/poses/Tree",  # недопустимые символы в имени
    ],
)
def test_invalid_audio_path_is_404_without_storage_call(
    monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    def fail(key: str) -> None:
        raise AssertionError(f"хранилище не должно вызываться: {key}")

    monkeypatch.setattr(storage, "get_audio", fail)

    assert client.get(path).status_code == 404
