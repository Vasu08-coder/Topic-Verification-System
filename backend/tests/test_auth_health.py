from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.routes.auth import limiter as auth_limiter


class DummySession:
    def __enter__(self) -> "DummySession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, *_args, **_kwargs) -> None:
        return None

    def query(self, *_args, **_kwargs) -> "DummyQuery":
        return DummyQuery()


class DummyQuery:
    def filter(self, *_args, **_kwargs) -> "DummyQuery":
        return self

    def first(self):
        return None

    def one_or_none(self):
        return None


def test_health_endpoint_returns_ok(monkeypatch) -> None:
    monkeypatch.setattr("app.main.SessionLocal", lambda: DummySession())
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["db"] == "connected"


def test_login_invalid_credentials_returns_generic_message(monkeypatch) -> None:
    monkeypatch.setattr("app.main.SessionLocal", lambda: DummySession())
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "does-not-exist", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_rate_limit_returns_json_error(monkeypatch) -> None:
    monkeypatch.setattr("app.main.SessionLocal", lambda: DummySession())
    auth_limiter.reset()

    app.state.limiter = auth_limiter
    app.dependency_overrides[get_db] = lambda: DummySession()

    with TestClient(app) as client:
        for _ in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": "does-not-exist", "password": "wrong-password"},
            )
        throttled = client.post(
            "/api/auth/login",
            json={"username": "does-not-exist", "password": "wrong-password"},
        )

    assert throttled.status_code == 429
    payload = throttled.json()
    assert payload["error"] is True
    assert payload["code"] == "rate_limit_exceeded"
    assert "Too many requests" in payload["message"]

    app.dependency_overrides.clear()
