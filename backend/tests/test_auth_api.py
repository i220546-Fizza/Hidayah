from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text

from app.models import AuthIdentity, User, UserPreference, UserSession
from tests.helpers import GOOD_PASSWORD, WEB, login, register, signup_and_login


# ---------- Registration ----------

def test_register_creates_account_without_leaking_secrets(client, session):
    r = register(client, "Alice@Example.COM", display_name="  Alice  ")
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"  # normalised
    assert body["display_name"] == "Alice"
    assert body["roles"] == ["user"]
    assert "password" not in r.text and "hash" not in r.text

    identity = session.scalar(select(AuthIdentity).where(AuthIdentity.provider_subject == "alice@example.com"))
    assert identity.password_hash.startswith("$argon2id$")
    assert GOOD_PASSWORD not in identity.password_hash
    assert session.scalar(select(UserPreference).where(UserPreference.user_id == identity.user_id)) is not None


def test_register_duplicate_email_is_conflict_case_insensitive(client):
    assert register(client, "dup@example.com").status_code == 201
    r = register(client, "DUP@example.com")
    assert r.status_code == 409


@pytest.mark.parametrize("pw", ["short", "          ", "x" * 200])
def test_register_rejects_weak_passwords_with_reasons(client, pw):
    r = register(client, "weak@example.com", pw)
    assert r.status_code == 422
    assert r.json()["detail"]


def test_register_rejects_password_equal_to_email(client):
    r = register(client, "same-as-password@example.com", "same-as-password@example.com")
    assert r.status_code == 422 and r.json()["errors"]


def test_register_rejects_invalid_email(client):
    assert register(client, "not-an-email").status_code == 422


# ---------- Login ----------

def test_login_mobile_returns_refresh_token_in_body(client):
    _, tokens = signup_and_login(client)
    assert tokens["token_type"] == "bearer" and tokens["expires_in"] == 15 * 60
    assert tokens["refresh_token"]


def test_login_web_uses_httponly_strict_cookie_and_hides_refresh_token(client):
    register(client)
    r = login(client, headers=WEB)
    assert r.status_code == 200
    assert r.json()["refresh_token"] is None
    cookie = r.headers["set-cookie"].lower()
    assert "hidayah_refresh=" in cookie
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api/v1/auth" in cookie
    assert r.headers["cache-control"] == "no-store"


def test_wrong_password_and_unknown_email_give_the_same_error(client):
    register(client)
    wrong = login(client, password="not-the-password")
    unknown = login(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.json()["detail"] == "Incorrect email or password."


def test_inactive_account_cannot_log_in(client, session):
    register(client)
    session.scalar(select(User)).is_active = False
    session.commit()
    assert login(client).status_code == 401


def test_login_is_rate_limited(client):
    register(client)
    codes = [login(client, password="wrong-password-x").status_code for _ in range(12)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
    r = login(client, password="wrong-password-x")
    assert "retry-after" in r.headers


def test_rate_limit_is_per_account_not_global(client):
    register(client, "a@example.com")
    register(client, "b@example.com")
    for _ in range(10):
        login(client, "a@example.com", "wrong-password-x")
    assert login(client, "a@example.com", GOOD_PASSWORD).status_code == 429
    assert login(client, "b@example.com", GOOD_PASSWORD).status_code == 200


# ---------- Access tokens ----------

def test_protected_endpoint_requires_token(client):
    assert client.get("/api/v1/users/me").status_code == 401


@pytest.mark.parametrize("header", ["Bearer garbage", "Bearer a.b.c", "Basic abc", "Bearer "])
def test_bad_authorization_headers_rejected(client, header):
    assert client.get("/api/v1/users/me", headers={"Authorization": header}).status_code == 401


def test_valid_token_returns_profile(client):
    headers, _ = signup_and_login(client)
    r = client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 200 and r.json()["email"] == "user@example.com"


def test_expired_access_token_rejected(client, session):
    from app.security.tokens import create_access_token

    signup_and_login(client)
    row = session.scalar(select(UserSession))
    old = create_access_token(row.user_id, row.id, now=datetime.now(timezone.utc) - timedelta(hours=1))
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {old}"}).status_code == 401


def test_refresh_token_cannot_be_used_as_access_token(client):
    _, tokens = signup_and_login(client)
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401


def test_session_expiry_enforced_on_access_and_refresh(client, session):
    headers, tokens = signup_and_login(client)
    row = session.scalar(select(UserSession))
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.commit()
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


# ---------- Refresh rotation and reuse detection ----------

def test_refresh_rotates_tokens(client):
    headers, tokens = signup_and_login(client)
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    new_headers = {"Authorization": f"Bearer {new['access_token']}"}
    assert client.get("/api/v1/users/me", headers=new_headers).status_code == 200
    # the previous session is retired immediately
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401


def test_reusing_an_old_refresh_token_revokes_every_session(client):
    _, tokens = signup_and_login(client)
    first = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()
    # attacker (or buggy client) replays the retired token
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert replay.status_code == 401
    # the legitimate newest session is now dead too
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {first['access_token']}"}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}).status_code == 401


def test_refresh_with_unknown_or_missing_token_rejected(client):
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "nope"}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={}).status_code == 401
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_web_refresh_works_from_cookie_with_client_header(client):
    register(client)
    assert login(client, headers=WEB).status_code == 200
    r = client.post("/api/v1/auth/refresh", headers=WEB)
    assert r.status_code == 200 and r.json()["access_token"]


def test_web_cookie_is_ignored_without_the_client_header(client):
    """Cross-site requests cannot add custom headers, so cookie mode stays CSRF-safe."""
    register(client)
    login(client, headers=WEB)
    assert client.post("/api/v1/auth/refresh").status_code == 401


# ---------- Logout ----------

def test_logout_revokes_session_immediately_and_is_idempotent(client):
    headers, tokens = signup_and_login(client)
    assert client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_logout_all_ends_every_device(client):
    headers, _ = signup_and_login(client)
    second = login(client).json()
    assert client.post("/api/v1/auth/logout-all", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {second['access_token']}"}).status_code == 401


# ---------- Storage hygiene ----------

def test_refresh_tokens_are_stored_hashed_only(client, session):
    _, tokens = signup_and_login(client)
    stored = session.scalars(select(UserSession.refresh_token_hash)).all()
    assert tokens["refresh_token"] not in stored
    assert all(len(h) == 64 for h in stored)
    assert session.scalar(text("select count(*) from auth_identities where password_hash = :p"), {"p": GOOD_PASSWORD}) == 0
