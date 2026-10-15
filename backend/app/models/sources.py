import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, TimestampMixin
from app.models.enums import (
    Permission,
    SourceCategory,
    SourceStatus,
    VerificationStatus,
    pg_enum,
)


class Source(TimestampMixin, Base):
    """
    One registered work (a Quran text, a translation, a tafsir, a hadith collection...).

    LICENCE RULE (enforced by the database): a source can only be 'approved' once its
    licence has been verified by a person AND commercial use, permanent storage, search
    indexing and answer-assistant (RAG) retrieval are each explicitly 'allowed'.
    Unknown or unclear rights can never reach production.
    """

    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint(
            "approval_status <> 'approved' OR ("
            "commercial_use = 'allowed' AND license_verified_at IS NOT NULL "
            "AND license_name IS NOT NULL AND rights_holder IS NOT NULL "
            "AND storage_permission = 'allowed' AND indexing_permission = 'allowed' "
            "AND rag_permission = 'allowed')",
            name="approved_requires_verified_commercial_licence",
        ),
        CheckConstraint(
            "approval_status <> 'approved' OR verification_status = 'verified'",
            name="approved_requires_verified_content",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[SourceCategory] = mapped_column(
        pg_enum(SourceCategory, "source_category"), nullable=False, index=True
    )
    author_or_publisher: Mapped[str | None] = mapped_column(String(300))
    translator: Mapped[str | None] = mapped_column(String(300))
    edition: Mapped[str | None] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    original_url: Mapped[str | None] = mapped_column(String(1000))

    # --- Licensing and rights (recorded BEFORE any import) ---
    rights_holder: Mapped[str | None] = mapped_column(String(300))
    license_name: Mapped[str | None] = mapped_column(String(200))
    license_url: Mapped[str | None] = mapped_column(String(1000))
    commercial_use: Mapped[Permission] = mapped_column(
        pg_enum(Permission, "commercial_use"), default=Permission.UNKNOWN, nullable=False
    )
    redistribution: Mapped[Permission] = mapped_column(
        pg_enum(Permission, "redistribution"), default=Permission.UNKNOWN, nullable=False
    )
    # Our intended uses, recorded separately because a licence may allow some and not others.
    storage_permission: Mapped[Permission] = mapped_column(
        pg_enum(Permission, "storage_permission"),
        default=Permission.UNKNOWN,
        server_default=Permission.UNKNOWN.value,
        nullable=False,
    )
    indexing_permission: Mapped[Permission] = mapped_column(
        pg_enum(Permission, "indexing_permission"),
        default=Permission.UNKNOWN,
        server_default=Permission.UNKNOWN.value,
        nullable=False,
    )
    rag_permission: Mapped[Permission] = mapped_column(
        pg_enum(Permission, "rag_permission"),
        default=Permission.UNKNOWN,
        server_default=Permission.UNKNOWN.value,
        nullable=False,
    )
    attribution_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    attribution_text: Mapped[str | None] = mapped_column(Text)
    rights_notes: Mapped[str | None] = mapped_column(Text)
    license_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    license_verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # --- Review state ---
    verification_status: Mapped[VerificationStatus] = mapped_column(
        pg_enum(VerificationStatus, "verification_status"),
        default=VerificationStatus.UNVERIFIED,
        nullable=False,
    )
    approval_status: Mapped[SourceStatus] = mapped_column(
        pg_enum(SourceStatus, "approval_status"),
        default=SourceStatus.DRAFT,
        nullable=False,
        index=True,
    )

    versions: Mapped[list["SourceVersion"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["SourceReview"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SourceVersion(TimestampMixin, Base):
    """A specific uploaded or imported edition of a source, identified by checksum."""

    __tablename__ = "source_versions"
    __table_args__ = (
        # Same file for the same source cannot be registered twice (idempotent ingestion).
        UniqueConstraint("source_id", "checksum_sha256"),
        UniqueConstraint("source_id", "version_label"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    version_label: Mapped[str] = mapped_column(String(80), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship(back_populates="versions")


class SourceReview(Base):
    """Approval history: every status change is recorded with who made it and why."""

    __tablename__ = "source_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    from_status: Mapped[SourceStatus] = mapped_column(
        pg_enum(SourceStatus, "review_from_status"), nullable=False
    )
    to_status: Mapped[SourceStatus] = mapped_column(
        pg_enum(SourceStatus, "review_to_status"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped[Source] = relationship(back_populates="reviews")
