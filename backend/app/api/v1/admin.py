import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.repositories import users as repo
from app.schemas.auth import RoleChange, UserOut
from app.schemas.common import Page
from app.security.deps import require_admin
from app.services import users as service

# Every route here requires the admin role, checked on the server for each request.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=Page[UserOut])
def list_users(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    rows, total = repo.list_users(db, limit, offset)
    return {"items": [service.user_dto(u) for u in rows], "total": total, "limit": limit, "offset": offset}


@router.post("/users/{user_id}/roles", response_model=UserOut)
def grant_role(user_id: uuid.UUID, payload: RoleChange, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.user_dto(service.admin_set_role(db, actor, user_id, payload.role, grant=True))


@router.delete("/users/{user_id}/roles/{role}", response_model=UserOut)
def revoke_role(user_id: uuid.UUID, role: str, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.user_dto(service.admin_set_role(db, actor, user_id, role, grant=False))
