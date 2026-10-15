import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthError, ValidationProblem
from app.models import AuditEvent, EmailToken, User
from app.repositories import users as repo
from app.security import passwords
from app.services import mailer
from app.services.auth import _now, normalize_email

VERIFY, RESET = "verify_email", "reset_password"
BAD_LINK = "This link is invalid or has expired. Please request a new one."


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _issue(db: Session, user: User, purpose: str) -> str:
    s = get_settings()
    now = _now()
    # a new request cancels older unused links of the same kind
    db.execute(update(EmailToken).where(EmailToken.user_id == user.id, EmailToken.purpose == purpose,
                                        EmailToken.used_at.is_(None)).values(used_at=now))
    token = secrets.token_urlsafe(32)
    db.add(EmailToken(user_id=user.id, purpose=purpose, token_hash=_hash(token),
                      expires_at=now + timedelta(hours=s.email_token_hours)))
    db.commit()
    return token


def _consume(db: Session, token: str, purpose: str) -> User:
    row = db.scalar(select(EmailToken).where(EmailToken.token_hash == _hash(token), EmailToken.purpose == purpose))
    now = datetime.now(timezone.utc)
    if row is None or row.used_at is not None or row.expires_at < now:
        raise AuthError(BAD_LINK)
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise AuthError(BAD_LINK)
    row.used_at = now
    return user


def send_verification(db: Session, user: User) -> None:
    if user.email_verified:
        return
    s = get_settings()
    token = _issue(db, user, VERIFY)
    mailer.send(user.email, "Confirm your Hidayah email",
                f"Open this link to confirm your email (valid {s.email_token_hours} hours):\n"
                f"{s.public_site_url}/verify-email?token={token}\n\nIf you did not create an account, ignore this message.")


def verify_email(db: Session, token: str) -> None:
    user = _consume(db, token, VERIFY)
    user.email_verified = True
    db.add(AuditEvent(actor_id=user.id, action="email_verified", entity_type="user", entity_id=str(user.id)))
    db.commit()


def request_reset(db: Session, email: str) -> None:
    """Always looks the same to the caller, whether or not the account exists."""
    user = repo.get_by_email(db, normalize_email(email))
    if user is None or not user.is_active or repo.get_password_identity(db, user.id) is None:
        return
    s = get_settings()
    token = _issue(db, user, RESET)
    mailer.send(user.email, "Reset your Hidayah password",
                f"Open this link to choose a new password (valid {s.email_token_hours} hours):\n"
                f"{s.public_site_url}/reset-password?token={token}\n\nIf you did not ask for this, ignore this message.")


def reset_password(db: Session, token: str, new_password: str) -> None:
    row_user = _consume(db, token, RESET)
    problems = passwords.validate_password_policy(new_password, row_user.email)
    if problems:
        db.rollback()  # the link stays usable so the person can try again
        raise ValidationProblem("Choose a stronger password.", errors=problems)
    identity = repo.get_password_identity(db, row_user.id)
    identity.password_hash = passwords.hash_password(new_password)
    row_user.email_verified = True  # they received mail at this address
    repo.revoke_all_sessions(db, row_user.id, _now())  # a reset signs out every device
    db.add(AuditEvent(actor_id=row_user.id, action="password_reset", entity_type="user", entity_id=str(row_user.id)))
    db.commit()
