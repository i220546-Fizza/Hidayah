from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    PreferencesOut,
    PreferencesUpdate,
    UserOut,
    UserUpdate,
)
from app.security.deps import AuthContext, get_auth_context, get_current_user
from app.models import User
from app.services import users as service

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return service.user_dto(user)


@router.patch("", response_model=UserOut)
def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.user_dto(service.update_profile(db, user, payload.display_name))


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.get_preferences(db, user)


@router.put("/preferences", response_model=PreferencesOut)
def update_preferences(payload: PreferencesUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.update_preferences(db, user, payload)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: ChangePasswordRequest, ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    service.change_password(db, ctx.user, ctx.session.id, payload.current_password, payload.new_password)


@router.get("/export")
def export(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.export_data(db, user)


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(payload: DeleteAccountRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.delete_account(db, user, payload.password)
