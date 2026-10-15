"""Email verification and password reset. No real mail is sent: the mailer records into an in-memory outbox."""
import re
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import EmailToken, UserSession
from app.services import mailer
from tests.helpers import GOOD_PASSWORD, WEB, login, register, signup_and_login


@pytest.fixture(autouse=True)
def clear_outbox():
    mailer.outbox.clear()


def last_token():
    return re.search(r"token=([\w-]+)", mailer.outbox[-1]["body"]).group(1)


def test_register_sends_a_verification_link_and_it_works(client):
    headers, _ = signup_and_login(client, "v@example.com")
    assert mailer.outbox[0]["to"] == "v@example.com" and "/verify-email?token=" in mailer.outbox[0]["body"]
    assert client.get("/api/v1/users/me", headers=headers).json()["email_verified"] is False
    assert client.post("/api/v1/auth/verify-email", json={"token": last_token()}).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).json()["email_verified"] is True


def test_link_works_once_only(client):
    register(client, "once@example.com")
    t = last_token()
    assert client.post("/api/v1/auth/verify-email", json={"token": t}).status_code == 204
    assert client.post("/api/v1/auth/verify-email", json={"token": t}).status_code == 401


def test_bad_and_expired_links_are_refused(client, session):
    register(client, "exp@example.com")
    assert client.post("/api/v1/auth/verify-email", json={"token": "x" * 40}).status_code == 401
    row = session.scalar(select(EmailToken))
    row.expires_at = row.expires_at - timedelta(days=1)
    session.commit()
    assert client.post("/api/v1/auth/verify-email", json={"token": last_token()}).status_code == 401


def test_only_a_hash_is_stored(client, session):
    register(client, "hash@example.com")
    assert last_token() not in session.scalar(select(EmailToken)).token_hash


def test_resend_verification_cancels_the_old_link(client):
    headers, _ = signup_and_login(client, "re@example.com")
    old = last_token()
    assert client.post("/api/v1/auth/request-verification", headers=headers).status_code == 204
    new = last_token()
    assert old != new
    assert client.post("/api/v1/auth/verify-email", json={"token": old}).status_code == 401
    assert client.post("/api/v1/auth/verify-email", json={"token": new}).status_code == 204
    n = len(mailer.outbox)
    assert client.post("/api/v1/auth/request-verification", headers=headers).status_code == 204
    assert len(mailer.outbox) == n  # already verified: no more mail


def test_forgot_password_looks_the_same_for_unknown_emails(client):
    register(client, "known@example.com")
    mailer.outbox.clear()
    a = client.post("/api/v1/auth/forgot-password", json={"email": "known@example.com"})
    b = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert a.status_code == b.status_code == 204 and a.text == b.text
    assert [m["to"] for m in mailer.outbox] == ["known@example.com"]


def test_reset_changes_password_and_signs_out_everywhere(client, session):
    _, tokens = signup_and_login(client, "reset@example.com")
    mailer.outbox.clear()
    client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})
    new_pw = "a-brand-new-password-9"
    assert client.post("/api/v1/auth/reset-password", json={"token": last_token(), "new_password": new_pw}).status_code == 204
    assert login(client, "reset@example.com", GOOD_PASSWORD).status_code == 401
    assert login(client, "reset@example.com", new_pw).status_code == 200
    old_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert old_refresh.status_code == 401
    assert all(x.revoked_at is not None for x in session.scalars(select(UserSession)))


def test_weak_password_keeps_the_link_usable(client):
    register(client, "weak@example.com")
    mailer.outbox.clear()
    client.post("/api/v1/auth/forgot-password", json={"email": "weak@example.com"})
    t = last_token()
    r = client.post("/api/v1/auth/reset-password", json={"token": t, "new_password": "short"})
    assert r.status_code == 422
    assert client.post("/api/v1/auth/reset-password", json={"token": t, "new_password": "another-good-password-1"}).status_code == 204


def test_reset_link_cannot_verify_email_and_vice_versa(client):
    register(client, "cross@example.com")
    verify = last_token()
    mailer.outbox.clear()
    client.post("/api/v1/auth/forgot-password", json={"email": "cross@example.com"})
    reset = last_token()
    assert client.post("/api/v1/auth/verify-email", json={"token": reset}).status_code == 401
    assert client.post("/api/v1/auth/reset-password", json={"token": verify, "new_password": "yet-another-password-1"}).status_code == 401


def test_forgot_is_rate_limited(client):
    codes = [client.post("/api/v1/auth/forgot-password", json={"email": f"x{i}@example.com"}).status_code for i in range(12)]
    assert 429 in codes
