from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import DuaProvenance, pg_enum


class DuaCategory(Base):
    __tablename__ = "dua_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name_english: Mapped[str] = mapped_column(String(120), nullable=False)
    name_urdu: Mapped[str | None] = mapped_column(String(120))


class Dua(TimestampMixin, Base):
    """
    'sourced' duas must carry a reference (reference_text) and a source version.
    'editorial' duas are clearly labelled and never attributed to the Quran or Hadith.
    """

    __tablename__ = "duas"
    __table_args__ = (
        CheckConstraint(
            "provenance <> 'sourced' OR (reference_text IS NOT NULL AND source_version_id IS NOT NULL)",
            name="sourced_requires_reference",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("dua_categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    arabic_text: Mapped[str] = mapped_column(Text, nullable=False)
    transliteration: Mapped[str | None] = mapped_column(Text)
    translation_text: Mapped[str | None] = mapped_column(Text)
    translation_language: Mapped[str | None] = mapped_column(String(10))
    provenance: Mapped[DuaProvenance] = mapped_column(
        pg_enum(DuaProvenance, "dua_provenance"), nullable=False
    )
    reference_text: Mapped[str | None] = mapped_column(String(500))
    source_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_versions.id", ondelete="RESTRICT"), index=True
    )
