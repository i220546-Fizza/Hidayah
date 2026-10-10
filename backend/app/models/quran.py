from sqlalchemy import CheckConstraint, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Surah(Base):
    """Stable canonical identifiers: surah number 1-114."""

    __tablename__ = "surahs"
    __table_args__ = (
        CheckConstraint("number BETWEEN 1 AND 114", name="number_range"),
        CheckConstraint("verse_count > 0", name="verse_count_positive"),
    )

    number: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name_arabic: Mapped[str] = mapped_column(String(80), nullable=False)
    name_english: Mapped[str] = mapped_column(String(80), nullable=False)
    name_transliterated: Mapped[str | None] = mapped_column(String(80))
    verse_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class Verse(TimestampMixin, Base):
    """Arabic text of one verse, from one verified source version. Never model-generated."""

    __tablename__ = "verses"
    __table_args__ = (
        UniqueConstraint("surah_number", "verse_number", "source_version_id"),
        CheckConstraint("verse_number > 0", name="verse_number_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    surah_number: Mapped[int] = mapped_column(
        ForeignKey("surahs.number", ondelete="RESTRICT"), index=True, nullable=False
    )
    verse_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    text_arabic: Mapped[str] = mapped_column(Text, nullable=False)
    source_version_id: Mapped[int] = mapped_column(
        ForeignKey("source_versions.id", ondelete="RESTRICT"), index=True, nullable=False
    )


class VerseTranslation(TimestampMixin, Base):
    """Keyed by (surah, verse) so any Arabic edition can be paired with it."""

    __tablename__ = "verse_translations"
    __table_args__ = (
        UniqueConstraint("source_version_id", "surah_number", "verse_number"),
        CheckConstraint("verse_number > 0", name="verse_number_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    surah_number: Mapped[int] = mapped_column(
        ForeignKey("surahs.number", ondelete="RESTRICT"), nullable=False
    )
    verse_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_version_id: Mapped[int] = mapped_column(
        ForeignKey("source_versions.id", ondelete="RESTRICT"), index=True, nullable=False
    )


class TafsirEntry(TimestampMixin, Base):
    """A commentary passage covering a range of verses in one surah."""

    __tablename__ = "tafsir_entries"
    __table_args__ = (
        CheckConstraint("verse_start > 0", name="verse_start_positive"),
        CheckConstraint("verse_end >= verse_start", name="verse_range_valid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    surah_number: Mapped[int] = mapped_column(
        ForeignKey("surahs.number", ondelete="RESTRICT"), index=True, nullable=False
    )
    verse_start: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    verse_end: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_version_id: Mapped[int] = mapped_column(
        ForeignKey("source_versions.id", ondelete="RESTRICT"), index=True, nullable=False
    )
