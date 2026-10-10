from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class HadithCollection(Base):
    __tablename__ = "hadith_collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name_english: Mapped[str] = mapped_column(String(200), nullable=False)
    name_arabic: Mapped[str | None] = mapped_column(String(200))
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True, nullable=False
    )


class HadithRecord(TimestampMixin, Base):
    __tablename__ = "hadith_records"
    __table_args__ = (UniqueConstraint("collection_id", "hadith_number", "source_version_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("hadith_collections.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    book_number: Mapped[str | None] = mapped_column(String(20))
    book_name: Mapped[str | None] = mapped_column(String(300))
    # A string, because numbering schemes include values like "12a".
    hadith_number: Mapped[str] = mapped_column(String(30), nullable=False)
    arabic_text: Mapped[str | None] = mapped_column(Text)
    translation_text: Mapped[str | None] = mapped_column(Text)
    translation_language: Mapped[str | None] = mapped_column(String(10))
    narrator: Mapped[str | None] = mapped_column(String(300))
    source_version_id: Mapped[int] = mapped_column(
        ForeignKey("source_versions.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    gradings: Mapped[list["HadithGrading"]] = relationship(
        back_populates="hadith", cascade="all, delete-orphan"
    )


class HadithGrading(TimestampMixin, Base):
    """
    One grading by one named grader. A hadith can hold several, so differing
    scholarly assessments are shown side by side and never merged or invented.
    """

    __tablename__ = "hadith_gradings"
    __table_args__ = (UniqueConstraint("hadith_id", "grader"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hadith_id: Mapped[int] = mapped_column(
        ForeignKey("hadith_records.id", ondelete="CASCADE"), index=True, nullable=False
    )
    grader: Mapped[str] = mapped_column(String(200), nullable=False)
    grade: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    reference_note: Mapped[str | None] = mapped_column(Text)

    hadith: Mapped[HadithRecord] = relationship(back_populates="gradings")
