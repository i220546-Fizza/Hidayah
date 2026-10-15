"""One place to record who did what. Audit rows never contain passwords, tokens or emails."""
import uuid

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record(
    db: Session,
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | int | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=None if entity_id is None else str(entity_id),
            details=details,
        )
    )
