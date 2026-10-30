"""ORM models. Table names follow the SAD data view (Figure C5)."""
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, utcnow


class Role(StrEnum):
    ANALYST = "Analyst"
    QA = "QA Engineer"
    DEVELOPER = "Developer"
    ADMIN = "Administrator"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(32), default=Role.ANALYST)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuthSession(Base):
    """One row per issued token, so tokens can be revoked at logout and expire on inactivity (SEC-02)."""

    __tablename__ = "auth_sessions"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship()


class AuditLog(Base):
    """Append-only record of who did what and when (FR-15)."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    project_id: Mapped[int | None] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(40))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    user: Mapped[User | None] = relationship()


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped[User] = relationship()
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class RequirementInput(Base):
    """Raw requirements text, typed or extracted from an uploaded file (FR-03)."""

    __tablename__ = "inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10))  # "text" or "file"
    filename: Mapped[str | None] = mapped_column(String(255))
    stored_path: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    author: Mapped[User | None] = relationship()


class SRSVersion(Base):
    """Every save is a new row, never an in-place update (FR-05, SAD AD-3)."""

    __tablename__ = "srs_versions"
    __table_args__ = (UniqueConstraint("project_id", "version_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    sections: Mapped[list] = mapped_column(JSON)  # [{"number", "title", "content"}]
    status: Mapped[str] = mapped_column(String(12), default="draft")  # draft | approved
    source: Mapped[str] = mapped_column(String(12), default="generated")  # generated | edited
    note: Mapped[str] = mapped_column(String(300), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)

    author: Mapped[User | None] = relationship(foreign_keys=[created_by])
    approver: Mapped[User | None] = relationship(foreign_keys=[approved_by])
    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="srs_version", cascade="all, delete-orphan", passive_deletes=True, order_by="Requirement.id"
    )


class Requirement(Base):
    """One row per requirement ID per SRS version, so tests can link to it (FR-07, SAD AD-4)."""

    __tablename__ = "requirements"
    __table_args__ = (UniqueConstraint("srs_version_id", "req_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    srs_version_id: Mapped[int] = mapped_column(ForeignKey("srs_versions.id", ondelete="CASCADE"), index=True)
    req_id: Mapped[str] = mapped_column(String(20))
    type: Mapped[str] = mapped_column(String(20))  # functional | non-functional
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10), default="Should")

    srs_version: Mapped[SRSVersion] = relationship(back_populates="requirements")


class TestCase(Base):
    __tablename__ = "test_cases"
    __test__ = False  # not a pytest test class

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    srs_version_id: Mapped[int] = mapped_column(ForeignKey("srs_versions.id", ondelete="CASCADE"), index=True)
    tc_id: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(12))  # positive | negative | boundary
    preconditions: Mapped[str] = mapped_column(Text, default="")
    steps: Mapped[list] = mapped_column(JSON)
    expected_result: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    links: Mapped[list["TraceLink"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan", passive_deletes=True
    )


class TraceLink(Base):
    """Requirement-to-test link; the traceability matrix is computed from these rows (FR-07)."""

    __tablename__ = "trace_links"

    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"), primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), primary_key=True)

    test_case: Mapped[TestCase] = relationship(back_populates="links")
    requirement: Mapped[Requirement] = relationship()


class TestPlan(Base):
    """Generated test plan for an approved SRS version (FR-09)."""

    __tablename__ = "test_plans"
    __test__ = False

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    srs_version_id: Mapped[int] = mapped_column(ForeignKey("srs_versions.id", ondelete="CASCADE"), index=True)
    sections: Mapped[list] = mapped_column(JSON)  # [{"title", "content"}]
    requirement_ids: Mapped[list] = mapped_column(JSON)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Diagram(Base):
    """Latest UML diagram of each kind for a project, as editable Mermaid source (FR-10)."""

    __tablename__ = "diagrams"
    __table_args__ = (UniqueConstraint("project_id", "kind"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    srs_version_id: Mapped[int] = mapped_column(ForeignKey("srs_versions.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20))  # use_case | class | sequence
    source: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
