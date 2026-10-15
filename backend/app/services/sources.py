"""
Source registry rules. The database refuses an unlicensed 'approved' source; this layer
explains WHY in plain words and keeps the review history.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound, ValidationProblem
from app.models import Source, SourceReview, SourceVersion, User
from app.models.enums import Permission, SourceStatus, VerificationStatus
from app.schemas.sources import SourceCreate, SourceDescribe, SourceRights
from app.services import audit

# Fields whose change invalidates an earlier licence check.
RIGHTS_FIELDS = (
    "rights_holder", "license_name", "license_url", "commercial_use", "redistribution",
    "storage_permission", "indexing_permission", "rag_permission", "attribution_required",
    "attribution_text",
)
USE_FIELDS = (
    ("commercial_use", "commercial use"),
    ("storage_permission", "permanent storage"),
    ("indexing_permission", "search indexing"),
    ("rag_permission", "answer-assistant retrieval"),
)


def get(db: Session, source_id: int) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise NotFound("Source not found.")
    return source


def list_sources(db: Session, *, status: SourceStatus | None, category, limit: int, offset: int):
    stmt = select(Source)
    count = select(func.count()).select_from(Source)
    if status is not None:
        stmt = stmt.where(Source.approval_status == status)
        count = count.where(Source.approval_status == status)
    if category is not None:
        stmt = stmt.where(Source.category == category)
        count = count.where(Source.category == category)
    rows = db.scalars(stmt.order_by(Source.title).limit(limit).offset(offset)).all()
    return rows, db.scalar(count) or 0


def approved_sources(db: Session) -> list[Source]:
    return list(
        db.scalars(
            select(Source).where(Source.approval_status == SourceStatus.APPROVED).order_by(Source.title)
        )
    )


def create(db: Session, actor: User, data: SourceCreate) -> Source:
    source = Source(**data.model_dump())
    db.add(source)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise Conflict("A source with that identifier already exists.") from None
    audit.record(db, actor.id, "source_created", "source", source.id, {"slug": source.slug})
    db.commit()
    return source


def describe(db: Session, actor: User, source: Source, data: SourceDescribe) -> Source:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    audit.record(db, actor.id, "source_described", "source", source.id)
    db.commit()
    return source


def update_rights(db: Session, actor: User, source: Source, data: SourceRights) -> Source:
    changes = data.model_dump(exclude_unset=True)
    changed = {k: v for k, v in changes.items() if getattr(source, k) != v}
    if not changed:
        return source
    was_approved = source.approval_status == SourceStatus.APPROVED
    for field, value in changed.items():
        setattr(source, field, value)
    details: dict = {"fields": sorted(changed)}
    if was_approved and any(f in RIGHTS_FIELDS for f in changed):
        # A changed licence invalidates the earlier check: back to review, licence unverified.
        source.approval_status = SourceStatus.UNDER_REVIEW
        source.license_verified_at = None
        source.license_verified_by = None
        db.add(SourceReview(
            source_id=source.id, reviewer_id=actor.id, from_status=SourceStatus.APPROVED,
            to_status=SourceStatus.UNDER_REVIEW, note="Rights fields changed; licence must be verified again.",
        ))
        details["reverted_to_review"] = True
    audit.record(db, actor.id, "source_rights_updated", "source", source.id, details)
    db.commit()
    return source


def readiness(db: Session, source: Source) -> list[str]:
    """Everything still missing before this source may be approved, in plain words."""
    missing: list[str] = []
    if not source.rights_holder:
        missing.append("Record who holds the rights.")
    if not source.license_name:
        missing.append("Record the exact licence name.")
    if source.license_verified_at is None:
        missing.append("A person must verify the licence.")
    for field, label in USE_FIELDS:
        if getattr(source, field) != Permission.ALLOWED:
            missing.append(f"Permission for {label} must be 'allowed' (it is '{getattr(source, field).value}').")
    if source.verification_status != VerificationStatus.VERIFIED:
        missing.append("A person must verify the content.")
    return missing


def verify_licence(db: Session, actor: User, source: Source, note: str) -> Source:
    problems = []
    if not source.rights_holder:
        problems.append("Record who holds the rights first.")
    if not source.license_name:
        problems.append("Record the exact licence name first.")
    if problems:
        raise ValidationProblem("The licence cannot be verified yet.", errors=problems)
    source.license_verified_at = datetime.now(timezone.utc)
    source.license_verified_by = actor.id
    audit.record(db, actor.id, "source_licence_verified", "source", source.id, {"note": note})
    db.commit()
    return source


def verify_content(db: Session, actor: User, source: Source, note: str) -> Source:
    has_version = db.scalar(
        select(func.count()).select_from(SourceVersion).where(SourceVersion.source_id == source.id)
    )
    if not has_version:
        raise ValidationProblem(
            "There is no imported version to verify yet.",
            errors=["Content can only be verified after a version has been imported."],
        )
    source.verification_status = VerificationStatus.VERIFIED
    audit.record(db, actor.id, "source_content_verified", "source", source.id, {"note": note})
    db.commit()
    return source


def change_status(db: Session, actor: User, source: Source, to_status: SourceStatus, note: str) -> Source:
    if to_status == source.approval_status:
        raise ValidationProblem("The source already has that status.")
    if to_status == SourceStatus.APPROVED:
        missing = readiness(db, source)
        if missing:
            raise ValidationProblem("This source cannot be approved yet.", errors=missing)
    previous = source.approval_status
    source.approval_status = to_status
    db.add(SourceReview(
        source_id=source.id, reviewer_id=actor.id, from_status=previous, to_status=to_status, note=note,
    ))
    audit.record(
        db, actor.id, "source_status_changed", "source", source.id,
        {"from": previous.value, "to": to_status.value},
    )
    db.commit()
    return source


def reviews(db: Session, source: Source) -> list[SourceReview]:
    return list(
        db.scalars(
            select(SourceReview).where(SourceReview.source_id == source.id).order_by(SourceReview.id.desc())
        )
    )
