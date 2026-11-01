import storage
from fastapi.testclient import TestClient
from main import app
from pytest import MonkeyPatch

# TestClient без "with" не запускает lifespan, поэтому база для тестов не нужна
client = TestClient(app)


def test_image_is_returned_with_content_type(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        storage, "get_image", lambda name: (b"jpeg-bytes", "image/jpeg")
    )

    r = client.get("/api/images/Eagle Pose.jpg")

    assert r.status_code == 200
    assert r.content == b"jpeg-bytes"
    assert r.headers["content-type"] == "image/jpeg"


def test_cyrillic_name_is_decoded(monkeypatch: MonkeyPatch) -> None:
    requested: list[str] = []

    def fake_get_image(name: str) -> tuple[bytes, str]:
        requested.append(name)
        return b"png", "image/png"

    monkeypatch.setattr(storage, "get_image", fake_get_image)

    client.get("/api/images/Поза горы.png")

    assert requested == ["Поза горы.png"]


def test_missing_image_is_404(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "get_image", lambda name: None)

    r = client.get("/api/images/nope.jpg")

    assert r.status_code == 404
