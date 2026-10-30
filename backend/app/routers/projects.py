"""Project management and membership (FR-02, SEC-07)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit
from app.db import get_db, utcnow
from app.deps import get_current_user, get_project
from app.models import Project, ProjectMember, Role, User

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("Project name cannot be blank")
    return value


class ProjectIn(BaseModel):
    name: str = Field(max_length=120)
    description: str = Field("", max_length=2000)

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return _clean_name(value)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    archived: bool | None = None

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str | None) -> str | None:
        return _clean_name(value)


class MemberIn(BaseModel):
    email: EmailStr


class MemberOut(BaseModel):
    id: int
    name: str
    email: str
    role: str


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    archived: bool
    owner_id: int
    owner_name: str
    member_count: int
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectOut):
    members: list[MemberOut]


def _member_count(db: Session, project_id: int) -> int:
    return db.scalar(select(func.count()).where(ProjectMember.project_id == project_id)) or 0


def _out(db: Session, project: Project) -> ProjectOut:
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        archived=project.archived,
        owner_id=project.owner_id,
        owner_name=project.owner.name,
        member_count=_member_count(db, project.id),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _detail(db: Session, project: Project) -> ProjectDetail:
    members = [
        MemberOut(id=m.user.id, name=m.user.name, email=m.user.email, role=m.user.role)
        for m in sorted(project.members, key=lambda m: m.added_at)
    ]
    return ProjectDetail(**_out(db, project).model_dump(), members=members)


def _require_owner_or_admin(project: Project, user: User) -> None:
    if project.owner_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the project owner or an Administrator can do this.")


@router.get("", response_model=list[ProjectOut])
def list_projects(
    include_archived: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ProjectOut]:
    query = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id)
        .order_by(Project.updated_at.desc())
    )
    if not include_archived:
        query = query.where(Project.archived.is_(False))
    return [_out(db, p) for p in db.scalars(query)]


@router.post("", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ProjectDetail:
    project = Project(name=body.name, description=body.description, owner_id=user.id)
    project.members.append(ProjectMember(user_id=user.id))
    db.add(project)
    db.flush()
    audit.record(db, user, "create", "project", project.id, project.id, project.name)
    db.commit()
    db.refresh(project)
    return _detail(db, project)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project_detail(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> ProjectDetail:
    return _detail(db, project)


@router.patch("/{project_id}", response_model=ProjectDetail)
def update_project(
    body: ProjectUpdate,
    project: Project = Depends(get_project),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    _require_owner_or_admin(project, user)
    changes = body.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(project, field, value)
    project.updated_at = utcnow()
    action = "archive" if changes.get("archived") else "edit"
    audit.record(db, user, action, "project", project.id, project.id, ", ".join(changes))
    db.commit()
    return _detail(db, project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project: Project = Depends(get_project), user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    _require_owner_or_admin(project, user)
    audit.record(db, user, "delete", "project", project.id, project.id, project.name)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/members", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def add_member(
    body: MemberIn,
    project: Project = Depends(get_project),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    _require_owner_or_admin(project, user)
    new_member = db.scalar(select(User).where(User.email == body.email.lower()))
    if new_member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No registered user has that email.")
    if db.get(ProjectMember, (project.id, new_member.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "That user is already a member.")
    project.members.append(ProjectMember(user_id=new_member.id))
    audit.record(db, user, "add_member", "project", project.id, project.id, new_member.email)
    db.commit()
    db.refresh(project)
    return _detail(db, project)


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectDetail)
def remove_member(
    user_id: int,
    project: Project = Depends(get_project),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    _require_owner_or_admin(project, user)
    if user_id == project.owner_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The project owner cannot be removed.")
    membership = db.get(ProjectMember, (project.id, user_id))
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That user is not a member.")
    db.delete(membership)
    audit.record(db, user, "remove_member", "project", project.id, project.id, str(user_id))
    db.commit()
    db.refresh(project)
    return _detail(db, project)
