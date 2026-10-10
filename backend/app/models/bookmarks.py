import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Bookmark(Base):
    """A saved verse, hadith or dua. Exactly one target; one bookmark per user per item."""

    __tablename__ = "bookmarks"
    __table_args__ = (
        CheckConstraint("num_nonnulls(verse_id, hadith_id, dua_id) = 1", name="exactly_one_target"),
        Index(
            "uq_bookmarks_user_verse", "user_id", "verse_id", unique=True,
            postgresql_where=text("verse_id IS NOT NULL"),
        ),
        Index(
            "uq_bookmarks_user_hadith", "user_id", "hadith_id", unique=True,
            postgresql_where=text("hadith_id IS NOT NULL"),
        ),
        Index(
            "uq_bookmarks_user_dua", "user_id", "dua_id", unique=True,
            postgresql_where=text("dua_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    verse_id: Mapped[int | None] = mapped_column(ForeignKey("verses.id", ondelete="CASCADE"))
    hadith_id: Mapped[int | None] = mapped_column(
        ForeignKey("hadith_records.id", ondelete="CASCADE")
    )
    dua_id: Mapped[int | None] = mapped_column(ForeignKey("duas.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
