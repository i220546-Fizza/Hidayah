"""Registration, login, refresh-token rotation and logout."""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthError, Conflict, ValidationProblem
from app.models import User, UserSession
from app.repositories import users as repo
from app.security import passwords, tokens

GENERIC_LOGIN_ERROR = "Incorrect email or password."


@dataclass
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    user: User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register(db: Session, *, email: str, password: str, display_name: str | None) -> User:
    email = normalize_email(email)
    problems = passwords.validate_password_policy(password, email)
    if problems:
        raise ValidationProblem("Choose a stronger password.", errors=problems)

    role = repo.get_role(db, "user")
    if role is None:  # migrations seed this; a missing role is a deployment fault
        raise RuntimeError("base role 'user' is missing; run database migrations")

    try:
        if repo.get_by_email(db, email) is not None:
            raise Conflict("An account with this email already exists.")
        user = repo.create_password_user(db, email, display_name, passwords.hash_password(password), role)
        db.commit()
    except IntegrityError as exc:  # two simultaneous sign-ups for the same email
        db.rollback()
        raise Conflict("An account with this email already exists.") from exc
    return user


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = repo.get_by_email(db, normalize_email(email))
    identity = repo.get_password_identity(db, user.id) if user else None
    ok = passwords.verify_password(password, identity.password_hash if identity else None)
    if not (ok and user and user.is_active):
        raise AuthError(GENERIC_LOGIN_ERROR)
    if identity and identity.password_hash and passwords.needs_rehash(identity.password_hash):
        identity.password_hash = passwords.hash_password(password)
        db.commit()
    return user


def _issue(db: Session, user: User) -> IssuedTokens:
    s = get_settings()
    refresh = tokens.new_refresh_token()
    session_row = repo.create_session(
        db, user.id, tokens.hash_refresh_token(refresh), _now() + timedelta(days=s.refresh_token_days)
    )
    db.commit()
    return IssuedTokens(
        access_token=tokens.create_access_token(user.id, session_row.id),
        refresh_token=refresh,
        expires_in=s.access_token_minutes * 60,
        user=user,
    )


def login(db: Session, *, email: str, password: str) -> IssuedTokens:
    return _issue(db, authenticate(db, email=email, password=password))


def refresh(db: Session, refresh_token: str | None) -> IssuedTokens:
    """Rotate: the presented refresh token is retired and a new session is issued."""
    if not refresh_token:
        raise AuthError()
    row = repo.get_session_by_refresh_hash(db, tokens.hash_refresh_token(refresh_token))
    if row is None:
        raise AuthError()
    now = _now()
    if row.revoked_at is not None:
        # An already-used token came back: it may have been stolen. End every session.
        repo.revoke_all_sessions(db, row.user_id, now)
        db.commit()
        raise AuthError()
    if row.expires_at <= now:
        raise AuthError()
    user = repo.get_by_id(db, row.user_id)
    if user is None or not user.is_active:
        raise AuthError()
    repo.revoke_session(row, now)
    return _issue(db, user)  # commits the revocation and the new session together


def logout(db: Session, refresh_token: str | None) -> None:
    """Idempotent: succeeds even if the token is unknown or already revoked."""
    if not refresh_token:
        return
    row = repo.get_session_by_refresh_hash(db, tokens.hash_refresh_token(refresh_token))
    if row is not None:
        repo.revoke_session(row, _now())
        db.commit()


def logout_all(db: Session, user_id: uuid.UUID) -> None:
    repo.revoke_all_sessions(db, user_id, _now())
    db.commit()


def resolve_access_token(db: Session, token: str) -> tuple[User, UserSession]:
    """Validate a bearer token against the database (so revocation is immediate)."""
    try:
        user_id, session_id = tokens.decode_access_token(token)
    except tokens.TokenError as exc:
        raise AuthError() from exc
    row = repo.get_session(db, session_id)
    if row is None or row.user_id != user_id or row.revoked_at is not None or row.expires_at <= _now():
        raise AuthError()
    user = repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AuthError()
    return user, row
