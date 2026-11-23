from collections.abc import Iterator
from typing import Any

import pytest
import storage
from botocore.exceptions import ClientError
from exceptions import InvalidRangeError
from fastapi.testclient import TestClient
from main import app

# storage.get_audio подменяется в тестах эндпоинта, MinIO для тестов не нужен
client = TestClient(app)


def test_audio_without_range_returns_200_and_cache_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested: list[tuple[str, str | None]] = []

    def fake_get_audio(
        key: str, range_header: str | None = None
    ) -> tuple[Iterator[bytes], int, str | None]:
        requested.append((key, range_header))
        return iter([b"ID3", b"data"]), 7, None

    monkeypatch.setattr(storage, "get_audio", fake_get_audio)

    r = client.get("/api/audio/ru/poses/tree")

    assert r.status_code == 200
    assert r.content == b"ID3data"
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.headers["content-length"] == "7"
    assert r.headers["accept-ranges"] == "bytes"
    assert "cache-control" in r.headers
    assert "max-age=" in r.headers["cache-control"]
    assert "content-range" not in r.headers
    assert requested == [("audio/poses_ru/tree.mp3", None)]


def test_audio_with_valid_range_returns_206(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested: list[tuple[str, str | None]] = []

    def fake_get_audio(
        key: str, range_header: str | None = None
    ) -> tuple[Iterator[bytes], int, str | None]:
        requested.append((key, range_header))
        return iter([b"ID"]), 2, "bytes 0-1/7"

    monkeypatch.setattr(storage, "get_audio", fake_get_audio)

    r = client.get("/api/audio/ru/phrases/start", headers={"Range": "bytes=0-1"})

    assert r.status_code == 206
    assert r.content == b"ID"
    assert len(r.content) == 2
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.headers["content-length"] == "2"
    assert r.headers["content-range"] == "bytes 0-1/7"
    assert r.headers["accept-ranges"] == "bytes"
    assert "cache-control" in r.headers
    assert requested == [("audio/phrases_ru/start.mp3", "bytes=0-1")]


def test_audio_with_invalid_range_returns_416(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get_audio(
        key: str, range_header: str | None = None
    ) -> tuple[Iterator[bytes], int, str | None]:
        raise InvalidRangeError(range_header)

    monkeypatch.setattr(storage, "get_audio", fake_get_audio)

    r = client.get(
        "/api/audio/ru/phrases/start",
        headers={"Range": "bytes=999999-1000000"},
    )

    assert r.status_code == 416


@pytest.mark.parametrize(
    "bad_range",
    [
        "bytes=999-1000",  # за пределами файла (ошибка от S3/MinIO)
        "bytes=abc",  # невалидный синтаксис
        "bytes=0-1,5-10",  # несколько диапазонов вне скоупа
    ],
)
def test_storage_get_audio_invalid_range_raises(
    monkeypatch: pytest.MonkeyPatch, bad_range: str
) -> None:
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")

    class FakeS3:
        def get_object(self, **kwargs: Any) -> dict[str, Any]:
            raise ClientError(
                {
                    "Error": {
                        "Code": "InvalidRange",
                        "Message": "Requested Range Not Satisfiable",
                    }
                },
                "GetObject",
            )

    monkeypatch.setattr(storage, "get_s3_client", lambda: FakeS3())

    with pytest.raises(InvalidRangeError):
        storage.get_audio("audio/phrases_ru/start.mp3", range_header=bad_range)


def test_storage_get_audio_passes_range_to_s3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    captured_kwargs: dict[str, Any] = {}

    class FakeBody:
        def iter_chunks(self) -> Iterator[bytes]:
            yield b"ID"

    class FakeS3:
        def get_object(self, **kwargs: Any) -> dict[str, Any]:
            captured_kwargs.update(kwargs)
            return {
                "Body": FakeBody(),
                "ContentLength": 2,
                "ContentRange": "bytes 0-1/100",
            }

    monkeypatch.setattr(storage, "get_s3_client", lambda: FakeS3())

    res = storage.get_audio("audio/phrases_ru/start.mp3", range_header="bytes=0-1")

    assert res is not None
    chunks, length, content_range = res
    assert b"".join(chunks) == b"ID"
    assert length == 2
    assert content_range == "bytes 0-1/100"
    assert captured_kwargs == {
        "Bucket": "test-bucket",
        "Key": "audio/phrases_ru/start.mp3",
        "Range": "bytes=0-1",
    }


def test_missing_audio_is_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "get_audio", lambda key, range_header=None: None)

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
    def fail(key: str, range_header: str | None = None) -> None:
        raise AssertionError(f"хранилище не должно вызываться: {key}")

    monkeypatch.setattr(storage, "get_audio", fail)

    assert client.get(path).status_code == 404
