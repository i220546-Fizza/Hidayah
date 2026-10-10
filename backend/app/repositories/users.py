import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuthIdentity, Role, User, UserPreference, UserRole, UserSession


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_password_identity(db: Session, user_id: uuid.UUID) -> AuthIdentity | None:
    return db.scalar(
        select(AuthIdentity).where(AuthIdentity.user_id == user_id, AuthIdentity.provider == "password")
    )


def get_role(db: Session, name: str) -> Role | None:
    return db.scalar(select(Role).where(Role.name == name))


def role_names(user: User) -> list[str]:
    return sorted(r.name for r in user.roles)


def count_users_with_role(db: Session, name: str) -> int:
    return db.scalar(
        select(func.count())
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .join(User, User.id == UserRole.user_id)
        .where(Role.name == name, User.is_active.is_(True))
    ) or 0


def list_users(db: Session, limit: int, offset: int) -> tuple[list[User], int]:
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(select(User).order_by(User.created_at, User.id).limit(limit).offset(offset)).all()
    return list(rows), total


def create_password_user(db: Session, email: str, display_name: str | None, password_hash: str, role: Role) -> User:
    """Create the user, their password identity, default preferences and base role together."""
    user = User(email=email, display_name=display_name)
    user.roles.append(role)
    user.identities.append(
        AuthIdentity(provider="password", provider_subject=email, password_hash=password_hash)
    )
    db.add(user)
    db.flush()  # assigns user.id
    db.add(UserPreference(user_id=user.id))
    db.flush()
    return user


def get_preferences(db: Session, user_id: uuid.UUID) -> UserPreference | None:
    return db.get(UserPreference, user_id)


# --- Sessions -------------------------------------------------------------

def create_session(db: Session, user_id: uuid.UUID, refresh_hash: str, expires_at) -> UserSession:
    row = UserSession(user_id=user_id, refresh_token_hash=refresh_hash, expires_at=expires_at)
    db.add(row)
    db.flush()
    return row


def get_session(db: Session, session_id: uuid.UUID) -> UserSession | None:
    return db.get(UserSession, session_id)


def get_session_by_refresh_hash(db: Session, refresh_hash: str) -> UserSession | None:
    return db.scalar(select(UserSession).where(UserSession.refresh_token_hash == refresh_hash))


def revoke_session(row: UserSession, now) -> None:
    if row.revoked_at is None:
        row.revoked_at = now


def revoke_all_sessions(db: Session, user_id: uuid.UUID, now, *, except_id: uuid.UUID | None = None) -> int:
    rows = db.scalars(
        select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
    ).all()
    n = 0
    for row in rows:
        if except_id is not None and row.id == except_id:
            continue
        row.revoked_at = now
        n += 1
    return n
