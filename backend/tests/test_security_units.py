import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import DEV_SECRET, Settings
from app.security import passwords, tokens


def test_password_hash_verifies_and_is_not_plaintext():
    h = passwords.hash_password("a-long-enough-password")
    assert h.startswith("$argon2id$") and "a-long-enough-password" not in h
    assert passwords.verify_password("a-long-enough-password", h)
    assert not passwords.verify_password("another-password-x", h)


def test_unknown_user_verification_is_always_false():
    assert passwords.verify_password("anything-at-all", None) is False


def test_same_password_gets_different_hashes():
    assert passwords.hash_password("same-password-1") != passwords.hash_password("same-password-1")


@pytest.mark.parametrize(
    "pw,email,expect_problem",
    [("short", None, True), ("a" * 129, None, True), ("          ", None, True),
     ("user@example.com", "user@example.com", True), ("long-enough-password", "user@example.com", False)],
)
def test_password_policy(pw, email, expect_problem):
    assert bool(passwords.validate_password_policy(pw, email)) is expect_problem


def test_access_token_round_trip():
    uid, sid = uuid.uuid4(), uuid.uuid4()
    assert tokens.decode_access_token(tokens.create_access_token(uid, sid)) == (uid, sid)


def test_expired_token_rejected():
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    t = tokens.create_access_token(uuid.uuid4(), uuid.uuid4(), now=past)
    with pytest.raises(tokens.TokenError):
        tokens.decode_access_token(t)


def test_token_signed_with_other_key_rejected():
    from app.core.config import get_settings

    payload = {"iss": tokens.ISSUER, "sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()),
               "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(minutes=5), "typ": "access"}
    forged = jwt.encode(payload, "x" * 40, algorithm="HS256")
    assert get_settings().secret_key != "x" * 40
    with pytest.raises(tokens.TokenError):
        tokens.decode_access_token(forged)


def test_unsigned_alg_none_token_rejected():
    payload = {"iss": tokens.ISSUER, "sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()),
               "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(minutes=5), "typ": "access"}
    unsigned = jwt.encode(payload, None, algorithm="none")
    with pytest.raises(tokens.TokenError):
        tokens.decode_access_token(unsigned)


def test_garbage_token_rejected():
    for bad in ("", "abc", "a.b.c", "Bearer x"):
        with pytest.raises(tokens.TokenError):
            tokens.decode_access_token(bad)


def test_refresh_tokens_are_random_and_hashed_for_storage():
    a, b = tokens.new_refresh_token(), tokens.new_refresh_token()
    assert a != b and len(a) >= 60
    assert tokens.hash_refresh_token(a) != a and len(tokens.hash_refresh_token(a)) == 64


def test_production_refuses_default_or_short_secret():
    with pytest.raises(ValueError):
        Settings(env="production", secret_key=DEV_SECRET)
    with pytest.raises(ValueError):
        Settings(env="production", secret_key="short")
    assert Settings(env="production", secret_key="k" * 40).secure_cookies is True
    assert Settings(env="development").secure_cookies is False
