from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import create_app


def _client():
    return TestClient(create_app())


def test_health_is_ok_without_database():
    r = _client().get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_ok_when_database_and_pgvector_available(migrated_engine):
    r = _client().get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "checks": {"database": True, "pgvector": True}}


def test_ready_returns_503_when_database_is_down():
    class Broken:
        def execute(self, *a, **k):
            raise RuntimeError("database down")

    app = create_app()
    app.dependency_overrides[get_db] = lambda: Broken()
    r = TestClient(app).get("/ready")
    assert r.status_code == 503
    assert r.json()["status"] == "not_ready"
    assert r.json()["checks"] == {"database": False, "pgvector": False}


def test_cors_allows_configured_origin_only():
    c = _client()
    ok = c.options(
        "/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = c.options(
        "/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers


def test_docs_hidden_in_production(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("ENV", "production")
    get_settings.cache_clear()
    try:
        assert TestClient(create_app()).get("/docs").status_code == 404
    finally:
        monkeypatch.setenv("ENV", "test")
        get_settings.cache_clear()
