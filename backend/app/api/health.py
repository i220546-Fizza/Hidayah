import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])
log = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up. Does not touch the database."""
    return {"status": "ok"}


@router.get("/ready")
def ready(response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
    """Readiness: the database is reachable and pgvector is installed."""
    checks = {"database": False, "pgvector": False}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
        row = db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
        checks["pgvector"] = row is not None
    except Exception:  # noqa: BLE001 - report not-ready instead of crashing
        log.exception("readiness check failed")
    ok = all(checks.values())
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ok else "not_ready", "checks": checks}
