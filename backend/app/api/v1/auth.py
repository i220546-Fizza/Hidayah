from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from pydantic import BaseModel, EmailStr, Field

from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut
from app.security.deps import AuthContext, get_auth_context
from app.security.rate_limit import limiter
from app.services import auth as service
from app.services import email_tokens
from app.services.users import user_dto

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "hidayah_refresh"
CLIENT_HEADER = "x-hidayah-client"


def _client_ip(request: Request) -> str:
    # Behind a reverse proxy this is the proxy's address; see docs/security.md.
    return request.client.host if request.client else "unknown"


def _is_web(request: Request) -> bool:
    """The website keeps its refresh token in an HttpOnly cookie; mobile uses the JSON body.

    Requiring a custom header for cookie mode means a forged cross-site form post cannot use it.
    """
    return request.headers.get(CLIENT_HEADER, "").lower() == "web"


def _token_response(request: Request, response: Response, issued: service.IssuedTokens) -> TokenResponse:
    s = get_settings()
    body = TokenResponse(access_token=issued.access_token, expires_in=issued.expires_in)
    if _is_web(request):
        response.set_cookie(
            REFRESH_COOKIE,
            issued.refresh_token,
            max_age=s.refresh_token_days * 86400,
            httponly=True,
            secure=s.secure_cookies,
            samesite="strict",
            path="/api/v1/auth",
        )
    else:
        body.refresh_token = issued.refresh_token
    response.headers["Cache-Control"] = "no-store"
    return body


def _presented_refresh_token(request: Request, body: RefreshRequest | None) -> str | None:
    if _is_web(request):
        return request.cookies.get(REFRESH_COOKIE)
    return body.refresh_token if body else None


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    s = get_settings()
    limiter.check(f"register:{_client_ip(request)}", s.login_rate_limit, s.rate_limit_window_seconds)
    user = service.register(db, email=payload.email, password=payload.password, display_name=payload.display_name)
    email_tokens.send_verification(db, user)
    return user_dto(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    key = f"login:{_client_ip(request)}:{service.normalize_email(payload.email)}"
    limiter.check(key, s.login_rate_limit, s.rate_limit_window_seconds)
    issued = service.login(db, email=payload.email, password=payload.password)
    return _token_response(request, response, issued)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, body: RefreshRequest | None = None, db: Session = Depends(get_db)):
    issued = service.refresh(db, _presented_refresh_token(request, body))
    return _token_response(request, response, issued)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, body: RefreshRequest | None = None, db: Session = Depends(get_db)):
    service.logout(db, _presented_refresh_token(request, body))
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    service.logout_all(db, ctx.user.id)


class TokenIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(TokenIn):
    new_password: str = Field(max_length=256)


@router.post("/request-verification", status_code=status.HTTP_204_NO_CONTENT)
def request_verification(request: Request, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    s = get_settings()
    limiter.check(f"verify:{ctx.user.id}", 5, s.rate_limit_window_seconds)
    email_tokens.send_verification(db, ctx.user)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(payload: TokenIn, request: Request, db: Session = Depends(get_db)):
    s = get_settings()
    limiter.check(f"verify-token:{_client_ip(request)}", s.login_rate_limit, s.rate_limit_window_seconds)
    email_tokens.verify_email(db, payload.token)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(payload: ForgotIn, request: Request, db: Session = Depends(get_db)):
    s = get_settings()
    limiter.check(f"forgot:{_client_ip(request)}", s.login_rate_limit, s.rate_limit_window_seconds)
    email_tokens.request_reset(db, payload.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetIn, request: Request, db: Session = Depends(get_db)):
    s = get_settings()
    limiter.check(f"reset:{_client_ip(request)}", s.login_rate_limit, s.rate_limit_window_seconds)
    email_tokens.reset_password(db, payload.token, payload.new_password)
