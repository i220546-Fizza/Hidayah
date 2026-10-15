from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditEvent, User
from app.models.enums import SourceCategory, SourceStatus
from app.schemas.common import Page
from app.schemas.sources import (
    ApprovalReadiness,
    AuditOut,
    Note,
    PublicSourceOut,
    ReviewOut,
    SourceCreate,
    SourceDescribe,
    SourceOut,
    SourceRights,
    StatusChange,
)
from app.security.deps import require_admin
from app.services import sources as service

public_router = APIRouter(prefix="/sources", tags=["sources"])
admin_router = APIRouter(prefix="/admin", tags=["admin: sources"], dependencies=[Depends(require_admin)])


@public_router.get("", response_model=list[PublicSourceOut])
def public_sources(db: Session = Depends(get_db)):
    """The credits page: only approved sources, with the attribution we owe."""
    return service.approved_sources(db)


@admin_router.get("/sources", response_model=Page[SourceOut])
def list_sources(
    status_filter: SourceStatus | None = Query(None, alias="status"),
    category: SourceCategory | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total = service.list_sources(db, status=status_filter, category=category, limit=limit, offset=offset)
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


@admin_router.post("/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.create(db, actor, payload)


@admin_router.get("/sources/{source_id}", response_model=SourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)):
    return service.get(db, source_id)


@admin_router.patch("/sources/{source_id}", response_model=SourceOut)
def describe_source(source_id: int, payload: SourceDescribe, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.describe(db, actor, service.get(db, source_id), payload)


@admin_router.patch("/sources/{source_id}/rights", response_model=SourceOut)
def update_rights(source_id: int, payload: SourceRights, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.update_rights(db, actor, service.get(db, source_id), payload)


@admin_router.get("/sources/{source_id}/readiness", response_model=ApprovalReadiness)
def readiness(source_id: int, db: Session = Depends(get_db)):
    missing = service.readiness(db, service.get(db, source_id))
    return {"ready": not missing, "missing": missing}


@admin_router.post("/sources/{source_id}/verify-licence", response_model=SourceOut)
def verify_licence(source_id: int, payload: Note, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.verify_licence(db, actor, service.get(db, source_id), payload.note)


@admin_router.post("/sources/{source_id}/verify-content", response_model=SourceOut)
def verify_content(source_id: int, payload: Note, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.verify_content(db, actor, service.get(db, source_id), payload.note)


@admin_router.post("/sources/{source_id}/status", response_model=SourceOut)
def change_status(source_id: int, payload: StatusChange, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    return service.change_status(db, actor, service.get(db, source_id), payload.to_status, payload.note)


@admin_router.get("/sources/{source_id}/reviews", response_model=list[ReviewOut])
def source_reviews(source_id: int, db: Session = Depends(get_db)):
    return service.reviews(db, service.get(db, source_id))


@admin_router.get("/audit", response_model=Page[AuditOut])
def audit_log(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    from sqlalchemy import func

    rows = db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).offset(offset)).all()
    total = db.scalar(select(func.count()).select_from(AuditEvent)) or 0
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


@admin_router.post("/sources/{source_id}/imports", status_code=status.HTTP_201_CREATED)
def import_source_file(
    source_id: int,
    raw: bytes = Body(..., media_type="application/octet-stream"),
    kind: str = Query(...),
    version_label: str = Query(..., min_length=1, max_length=60),
    filename: str = Query("upload", max_length=300),
    language: str | None = Query(None, max_length=10),
    collection_slug: str | None = Query(None, max_length=80),
    collection_name: str | None = Query(None, max_length=200),
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Send the file's bytes as the request body. The licence gate runs before anything is read."""
    from app.ingest.service import import_file

    result = import_file(
        db, actor, service.get(db, source_id), kind=kind, raw=raw, filename=filename,
        version_label=version_label, language=language,
        collection_slug=collection_slug, collection_name=collection_name,
    )
    return {"version_id": result.version.id, "unchanged": result.unchanged, "counts": result.counts}


@admin_router.get("/sources/{source_id}/imports/check")
def import_check(source_id: int, db: Session = Depends(get_db)):
    """Tell the admin, before uploading, whether this source may be imported."""
    from app.ingest.service import import_blockers

    blockers = import_blockers(service.get(db, source_id))
    return {"allowed": not blockers, "blockers": blockers}
