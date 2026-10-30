"""Audit logger (FR-15). Callers commit the surrounding transaction."""
from sqlalchemy.orm import Session

from app.models import AuditLog, User


def record(
    db: Session,
    user: User | None,
    action: str,
    entity: str,
    entity_id: object = None,
    project_id: int | None = None,
    detail: str = "",
) -> None:
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            project_id=project_id,
            action=action,
            entity=entity,
            entity_id=None if entity_id is None else str(entity_id),
            detail=detail[:500],
        )
    )
