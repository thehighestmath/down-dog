from cors import DEFAULT_DEV_ORIGINS, parse_origins, setup_cors
from fastapi import FastAPI
from fastapi.testclient import TestClient

ALLOWED = "https://app.example.com"
OTHER = "https://other.example.com"
FOREIGN = "https://evil.example.org"


def make_client(raw: str | None) -> TestClient:
    app = FastAPI()
    setup_cors(app, raw if raw is not None else "")

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/track")
    def track() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


def test_parse_multiple_with_spaces_and_trailing_slash() -> None:
    assert parse_origins(f"{ALLOWED}, {OTHER}/ ,") == [ALLOWED, OTHER]


def test_parse_empty_falls_back_to_dev() -> None:
    assert parse_origins(None) == DEFAULT_DEV_ORIGINS
    assert parse_origins("  ") == DEFAULT_DEV_ORIGINS


def test_allowed_origin_gets_header() -> None:
    client = make_client(f"{ALLOWED},{OTHER}")
    for origin in (ALLOWED, OTHER):
        r = client.get("/ping", headers={"Origin": origin})
        assert r.headers["access-control-allow-origin"] == origin


def test_foreign_origin_has_no_header() -> None:
    r = make_client(ALLOWED).get("/ping", headers={"Origin": FOREIGN})
    assert "access-control-allow-origin" not in r.headers


def test_preflight_foreign_origin_rejected() -> None:
    r = make_client(ALLOWED).options(
        "/track",
        headers={
            "Origin": FOREIGN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 400
    assert "access-control-allow-origin" not in r.headers


def test_dev_defaults_allow_vite() -> None:
    r = make_client(None).get("/ping", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
