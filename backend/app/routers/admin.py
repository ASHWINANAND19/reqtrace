"""User administration and audit log (FR-12, FR-15). Administrator only."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.db import get_db
from app.deps import require_roles
from app.models import AuditLog, AuthSession, Project, Role, User
from app.permissions import ADMIN_ONLY
from app.routers.auth import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminUserOut(UserOut):
    is_active: bool


class UserUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class AuditEntry(BaseModel):
    id: int
    created_at: datetime
    user_name: str | None
    action: str
    entity: str
    entity_id: str | None
    project_id: int | None
    project_name: str | None
    detail: str


@router.get("/users", response_model=list[AdminUserOut])
def list_users(_: User = Depends(require_roles(*ADMIN_ONLY)), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    admin: User = Depends(require_roles(*ADMIN_ONLY)),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    if user.id == admin.id and (body.role not in (None, Role.ADMIN) or body.is_active is False):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot remove your own administrator access.")
    changes = []
    if body.role is not None and body.role != user.role:
        changes.append(f"role {user.role} -> {body.role}")
        user.role = body.role
    if body.is_active is not None and body.is_active != user.is_active:
        changes.append("activated" if body.is_active else "deactivated")
        user.is_active = body.is_active
        if not body.is_active:  # end the user's open sessions straight away
            for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user.id)):
                session.revoked = True
    if changes:
        audit.record(db, admin, "edit", "user", user.id, None, f"{user.email}: {', '.join(changes)}")
        db.commit()
    return user


@router.get("/audit", response_model=list[AuditEntry])
def audit_log(
    limit: int = 200,
    project_id: int | None = None,
    _: User = Depends(require_roles(*ADMIN_ONLY)),
    db: Session = Depends(get_db),
) -> list[AuditEntry]:
    query = select(AuditLog).order_by(AuditLog.id.desc()).limit(min(max(limit, 1), 1000))
    if project_id is not None:
        query = query.where(AuditLog.project_id == project_id)
    entries = list(db.scalars(query))
    names = {
        p.id: p.name
        for p in db.scalars(select(Project).where(Project.id.in_({e.project_id for e in entries if e.project_id})))
    }
    return [
        AuditEntry(
            id=e.id,
            created_at=e.created_at,
            user_name=e.user.name if e.user else None,
            action=e.action,
            entity=e.entity,
            entity_id=e.entity_id,
            project_id=e.project_id,
            project_name=names.get(e.project_id) if e.project_id else None,
            detail=e.detail,
        )
        for e in entries
    ]
