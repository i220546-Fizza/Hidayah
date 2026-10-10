"""Accounts, sessions and bookmarks must survive the backend process restarting.

No transaction rollback or dependency override here: requests really commit.
"""
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.db.session as db_session
from app.main import create_app
from tests.helpers import GOOD_PASSWORD


def _restart_backend() -> TestClient:
    """Throw away the connection pool and build a fresh app, like restarting the server."""
    if db_session._engine is not None:
        db_session._engine.dispose()
    db_session._engine = None
    db_session._SessionLocal = None
    return TestClient(create_app())


def test_account_session_and_bookmark_survive_backend_restart(migrated_engine):
    email = "persist-check@example.com"
    first = _restart_backend()
    try:
        assert first.post("/api/v1/auth/register", json={"email": email, "password": GOOD_PASSWORD}).status_code == 201
        tokens = first.post("/api/v1/auth/login", json={"email": email, "password": GOOD_PASSWORD}).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        first.put("/api/v1/users/me/preferences", headers=headers, json={"language": "ur", "arabic_font_size": 40})

        # real content row for the bookmark
        with migrated_engine.begin() as conn:
            conn.execute(text("INSERT INTO surahs (number,name_arabic,name_english,verse_count) VALUES (1,'x','Persist test',7)"))
            sid = conn.execute(text("INSERT INTO sources (slug,title,category,language,commercial_use,redistribution,attribution_required,verification_status,approval_status) VALUES ('persist-src','t','tafsir','en','unknown','unknown',true,'unverified','draft') RETURNING id")).scalar()
            vid = conn.execute(text("INSERT INTO source_versions (source_id,version_label,checksum_sha256) VALUES (:s,'v1','abc') RETURNING id"), {"s": sid}).scalar()
            verse_id = conn.execute(text("INSERT INTO verses (surah_number,verse_number,text_arabic,source_version_id) VALUES (1,1,'t',:v) RETURNING id"), {"v": vid}).scalar()
        assert first.post("/api/v1/bookmarks", headers=headers, json={"type": "verse", "target_id": verse_id}).status_code == 201

        # ---- backend "restarts" ----
        second = _restart_backend()
        me = second.get("/api/v1/users/me", headers=headers)  # the OLD access token still works
        assert me.status_code == 200 and me.json()["email"] == email
        assert second.get("/api/v1/users/me/preferences", headers=headers).json()["language"] == "ur"
        assert second.get("/api/v1/bookmarks", headers=headers).json()["total"] == 1
        assert second.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
        assert second.post("/api/v1/auth/login", json={"email": email, "password": GOOD_PASSWORD}).status_code == 200
    finally:
        with migrated_engine.begin() as conn:
            conn.execute(text("DELETE FROM users WHERE email = :e"), {"e": email})
            conn.execute(text("DELETE FROM verses"))
            conn.execute(text("DELETE FROM surahs"))
            conn.execute(text("DELETE FROM source_versions"))
            conn.execute(text("DELETE FROM sources"))
        db_session._engine = None
        db_session._SessionLocal = None
