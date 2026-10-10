"""Profile, preferences, password change, data export and account deletion."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AuthError, Conflict, NotFound, PermissionDenied, ValidationProblem
from app.models import (
    AuditEvent,
    Bookmark,
    Conversation,
    QuizAttempt,
    ReadingProgress,
    User,
    UserPathProgress,
)
from app.repositories import bookmarks as bookmark_repo
from app.repositories import users as repo
from app.schemas.auth import PreferencesUpdate
from app.security import passwords
from app.services import auth as auth_service


def user_dto(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "email_verified": user.email_verified,
        "roles": repo.role_names(user),
        "created_at": user.created_at,
    }


def update_profile(db: Session, user: User, display_name: str | None) -> User:
    user.display_name = display_name
    db.commit()
    return user


def get_preferences(db: Session, user: User):
    prefs = repo.get_preferences(db, user.id)
    if prefs is None:  # accounts created before preferences existed
        from app.models import UserPreference

        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
        db.commit()
    return prefs


def update_preferences(db: Session, user: User, patch: PreferencesUpdate):
    prefs = get_preferences(db, user)
    changes = patch.model_dump(exclude_unset=True)
    # Validate the resulting state BEFORE touching the stored record.
    enabled = changes.get("reminders_enabled", prefs.reminders_enabled)
    reminder_time = changes.get("reminder_time", prefs.reminder_time)
    if enabled and reminder_time is None:
        raise ValidationProblem("Choose a reminder time before turning reminders on.")
    for field, value in changes.items():
        setattr(prefs, field, value)
    db.commit()
    return prefs


def change_password(db: Session, user: User, current_session_id, current: str, new: str) -> None:
    identity = repo.get_password_identity(db, user.id)
    if identity is None or not passwords.verify_password(current, identity.password_hash):
        raise AuthError("Current password is incorrect.")
    problems = passwords.validate_password_policy(new, user.email)
    if problems:
        raise ValidationProblem("Choose a stronger password.", errors=problems)
    identity.password_hash = passwords.hash_password(new)
    # Sign out every other device; keep the one making the change.
    from app.services.auth import _now

    repo.revoke_all_sessions(db, user.id, _now(), except_id=current_session_id)
    db.add(AuditEvent(actor_id=user.id, action="password_changed", entity_type="user", entity_id=str(user.id)))
    db.commit()


def export_data(db: Session, user: User) -> dict:
    """Everything we hold that belongs to this user, as plain JSON."""
    prefs = get_preferences(db, user)
    bookmarks = db.scalars(select(Bookmark).where(Bookmark.user_id == user.id).order_by(Bookmark.id)).all()
    conversations = db.scalars(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.created_at)
    ).all()
    attempts = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user.id).order_by(QuizAttempt.id)).all()
    paths = db.scalars(select(UserPathProgress).where(UserPathProgress.user_id == user.id)).all()
    reading = db.get(ReadingProgress, user.id)
    return {
        "profile": user_dto(user),
        "preferences": {
            "language": prefs.language,
            "arabic_font_size": prefs.arabic_font_size,
            "reminders_enabled": prefs.reminders_enabled,
            "reminder_time": prefs.reminder_time.isoformat() if prefs.reminder_time else None,
        },
        "bookmarks": [bookmark_repo.to_dto(b) for b in bookmarks],
        "conversations": [
            {
                "id": str(c.id),
                "title": c.title,
                "created_at": c.created_at,
                "messages": [
                    {"role": m.role.value, "content": m.content, "created_at": m.created_at} for m in c.messages
                ],
            }
            for c in conversations
        ],
        "quiz_attempts": [
            {"quiz_id": a.quiz_id, "score": a.score, "started_at": a.started_at, "completed_at": a.completed_at}
            for a in attempts
        ],
        "learning_path_progress": [
            {"path_id": p.path_id, "last_item_position": p.last_item_position, "completed_at": p.completed_at}
            for p in paths
        ],
        "reading_progress": (
            {"surah_number": reading.surah_number, "verse_number": reading.verse_number} if reading else None
        ),
    }


def delete_account(db: Session, user: User, password: str) -> None:
    identity = repo.get_password_identity(db, user.id)
    if identity is None or not passwords.verify_password(password, identity.password_hash):
        raise AuthError("Password is incorrect.")
    if "admin" in repo.role_names(user) and repo.count_users_with_role(db, "admin") <= 1:
        raise Conflict("You are the only administrator. Make another administrator first.")
    # Audit trail keeps the id only, never the email. actor_id becomes NULL when the user row goes.
    db.add(AuditEvent(actor_id=None, action="account_deleted", entity_type="user", entity_id=str(user.id)))
    db.delete(user)  # cascades to identities, sessions, bookmarks, conversations, progress
    db.commit()


# --- Administration ---------------------------------------------------------

def admin_set_role(db: Session, actor: User, target_id, role_name: str, *, grant: bool) -> User:
    target = repo.get_by_id(db, target_id)
    if target is None:
        raise NotFound("User not found.")
    role = repo.get_role(db, role_name)
    if role is None:
        raise NotFound("Role not found.")
    has = role in target.roles
    if grant and not has:
        target.roles.append(role)
    if not grant and has:
        if role_name == "user":
            raise PermissionDenied("The base 'user' role cannot be removed.")
        if role_name == "admin" and repo.count_users_with_role(db, "admin") <= 1:
            raise Conflict("Cannot remove the last administrator.")
        target.roles.remove(role)
    db.add(
        AuditEvent(
            actor_id=actor.id,
            action="role_granted" if grant else "role_revoked",
            entity_type="user",
            entity_id=str(target.id),
            details={"role": role_name},
        )
    )
    db.commit()
    return target


def bootstrap_admin(db: Session, email: str, password: str) -> User:
    """Used by the command-line tool: create the account if needed and make it an administrator."""
    email = auth_service.normalize_email(email)
    user = repo.get_by_email(db, email)
    if user is None:
        user = auth_service.register(db, email=email, password=password, display_name=None)
    admin = repo.get_role(db, "admin")
    if admin is None:
        raise RuntimeError("role 'admin' is missing; run database migrations")
    if admin not in user.roles:
        user.roles.append(admin)
        db.add(AuditEvent(actor_id=None, action="role_granted", entity_type="user",
                          entity_id=str(user.id), details={"role": "admin", "via": "cli"}))
        db.commit()
    return user
