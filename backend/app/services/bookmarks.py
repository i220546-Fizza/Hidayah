from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound
from app.models import Bookmark, User
from app.repositories import bookmarks as repo


def create(db: Session, user: User, type_: str, target_id: int) -> dict:
    if not repo.target_exists(db, type_, target_id):
        raise NotFound(f"That {type_} does not exist.")
    if repo.find(db, user.id, type_, target_id) is not None:
        raise Conflict("Already bookmarked.")
    col = repo.TARGETS[type_][1]
    bookmark = Bookmark(user_id=user.id, **{col: target_id})
    db.add(bookmark)
    try:
        db.commit()
    except IntegrityError as exc:  # double-tap race: the unique index catches it
        db.rollback()
        raise Conflict("Already bookmarked.") from exc
    db.refresh(bookmark)
    return repo.to_dto(bookmark)


def list_(db: Session, user: User, type_: str | None, limit: int, offset: int) -> dict:
    rows, total = repo.list_for_user(db, user.id, type_, limit, offset)
    return {"items": [repo.to_dto(b) for b in rows], "total": total, "limit": limit, "offset": offset}


def delete(db: Session, user: User, bookmark_id: int) -> None:
    row = repo.get_owned(db, user.id, bookmark_id)
    if row is None:  # also covers other people's bookmarks: do not reveal they exist
        raise NotFound("Bookmark not found.")
    db.delete(row)
    db.commit()
