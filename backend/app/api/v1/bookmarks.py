from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.bookmarks import BookmarkCreate, BookmarkOut, BookmarkType
from app.schemas.common import Page
from app.security.deps import get_current_user
from app.services import bookmarks as service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("", response_model=Page[BookmarkOut])
def list_bookmarks(
    type: BookmarkType | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_(db, user, type, limit, offset)


@router.post("", response_model=BookmarkOut, status_code=status.HTTP_201_CREATED)
def create_bookmark(payload: BookmarkCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.create(db, user, payload.type, payload.target_id)


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(bookmark_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.delete(db, user, bookmark_id)
