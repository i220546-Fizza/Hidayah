"""Access tokens (short-lived JWT) and refresh tokens (random, stored only as a hash)."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"
ISSUER = "hidayah-api"


class TokenError(Exception):
    """Token is missing, malformed, expired or otherwise not valid."""


def create_access_token(user_id: uuid.UUID, session_id: uuid.UUID, *, now: datetime | None = None) -> str:
    s = get_settings()
    issued = now or datetime.now(timezone.utc)
    payload = {
        "iss": ISSUER,
        "sub": str(user_id),
        "sid": str(session_id),
        "iat": issued,
        "exp": issued + timedelta(minutes=s.access_token_minutes),
        "typ": "access",
    }
    return jwt.encode(payload, s.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Return (user_id, session_id) or raise TokenError."""
    s = get_settings()
    try:
        payload = jwt.decode(
            token,
            s.secret_key,
            algorithms=[ALGORITHM],  # pinned: never trust the token's own "alg"
            issuer=ISSUER,
            options={"require": ["exp", "iat", "sub", "sid", "iss"]},
        )
        if payload.get("typ") != "access":
            raise TokenError("wrong token type")
        return uuid.UUID(payload["sub"]), uuid.UUID(payload["sid"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise TokenError("invalid token") from exc


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
