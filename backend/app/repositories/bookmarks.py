import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Bookmark, Dua, HadithRecord, Verse

# bookmark type -> (content model, bookmark column name)
TARGETS = {
    "verse": (Verse, "verse_id"),
    "hadith": (HadithRecord, "hadith_id"),
    "dua": (Dua, "dua_id"),
}


def target_exists(db: Session, type_: str, target_id: int) -> bool:
    model, _ = TARGETS[type_]
    return db.get(model, target_id) is not None


def to_dto(b: Bookmark) -> dict:
    for type_, (_, col) in TARGETS.items():
        value = getattr(b, col)
        if value is not None:
            return {"id": b.id, "type": type_, "target_id": value, "created_at": b.created_at}
    raise RuntimeError("bookmark without target")  # prevented by a database CHECK


def list_for_user(db: Session, user_id: uuid.UUID, type_: str | None, limit: int, offset: int):
    q = select(Bookmark).where(Bookmark.user_id == user_id)
    if type_:
        q = q.where(getattr(Bookmark, TARGETS[type_][1]).is_not(None))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(Bookmark.created_at.desc(), Bookmark.id.desc()).limit(limit).offset(offset)).all()
    return list(rows), total


def find(db: Session, user_id: uuid.UUID, type_: str, target_id: int) -> Bookmark | None:
    col = getattr(Bookmark, TARGETS[type_][1])
    return db.scalar(select(Bookmark).where(Bookmark.user_id == user_id, col == target_id))


def get_owned(db: Session, user_id: uuid.UUID, bookmark_id: int) -> Bookmark | None:
    return db.scalar(select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user_id))
