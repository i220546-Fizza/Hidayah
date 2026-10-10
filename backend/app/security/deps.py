"""FastAPI dependencies that enforce authentication and roles on the server."""
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthError, PermissionDenied
from app.db.session import get_db
from app.models import User, UserSession
from app.repositories.users import role_names
from app.services import auth as auth_service

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user: User
    session: UserSession


def get_auth_context(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AuthContext:
    if creds is None or creds.scheme.lower() != "bearer":
        raise AuthError("Sign in to continue.")
    user, session = auth_service.resolve_access_token(db, creds.credentials)
    return AuthContext(user=user, session=session)


def get_current_user(ctx: AuthContext = Depends(get_auth_context)) -> User:
    return ctx.user


def require_role(*allowed: str):
    """Dependency factory: the request is refused unless the user holds one of the roles."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if not set(role_names(user)) & set(allowed):
            raise PermissionDenied()
        return user

    return _check


require_admin = require_role("admin")
