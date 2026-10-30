"""SRS generation, versions and approval (FR-04, FR-05)."""
import difflib
import logging
import time
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit
from app.agents.base import AgentError, looks_like_injection
from app.agents.llm import LLMProvider, get_llm
from app.agents.srs_agent import IEEE830_SECTIONS, SRSAgent, assign_ids
from app.db import get_db, utcnow
from app.deps import get_project, require_roles
from app.models import Project, Requirement, RequirementInput, SRSVersion, User
from app.permissions import APPROVE_SRS, EDIT_SRS

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects/{project_id}/srs", tags=["srs"])

SECTION_TITLES = dict(IEEE830_SECTIONS)
MAX_INPUT_CHARS = 100_000  # roughly 25 pages


class SectionOut(BaseModel):
    number: str
    title: str
    content: str


class RequirementOut(BaseModel):
    req_id: str
    type: str
    title: str
    description: str
    priority: str

    model_config = {"from_attributes": True}


class VersionSummary(BaseModel):
    id: int
    version_no: int
    title: str
    status: str
    source: str
    note: str
    author_name: str | None
    created_at: datetime
    approved_by_name: str | None
    approved_at: datetime | None
    requirement_count: int


class VersionOut(VersionSummary):
    sections: list[SectionOut]
    requirements: list[RequirementOut]


def summary(version: SRSVersion) -> VersionSummary:
    return VersionSummary(
        id=version.id,
        version_no=version.version_no,
        title=version.title,
        status=version.status,
        source=version.source,
        note=version.note,
        author_name=version.author.name if version.author else None,
        created_at=version.created_at,
        approved_by_name=version.approver.name if version.approver else None,
        approved_at=version.approved_at,
        requirement_count=len(version.requirements),
    )


def version_out(version: SRSVersion) -> VersionOut:
    return VersionOut(
        **summary(version).model_dump(),
        sections=[SectionOut(**s) for s in version.sections],
        requirements=[RequirementOut.model_validate(r) for r in version.requirements],
    )


def load_version(db: Session, project: Project, version_id: int) -> SRSVersion:
    version = db.get(SRSVersion, version_id)
    if version is None or version.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SRS version not found.")
    return version


def create_version(
    db: Session,
    project: Project,
    user: User,
    title: str,
    sections: list[dict],
    requirements: list[dict],
    source: str,
    note: str = "",
) -> SRSVersion:
    latest = db.scalar(select(func.max(SRSVersion.version_no)).where(SRSVersion.project_id == project.id)) or 0
    version = SRSVersion(
        project_id=project.id,
        version_no=latest + 1,
        title=title,
        sections=sections,
        source=source,
        note=note,
        created_by=user.id,
    )
    version.requirements = [
        Requirement(
            project_id=project.id,
            req_id=r["req_id"],
            type=r["type"],
            title=r["title"],
            description=r["description"],
            priority=r["priority"],
        )
        for r in requirements
    ]
    db.add(version)
    db.flush()
    return version


@router.post("/generate", response_model=VersionOut, status_code=status.HTTP_201_CREATED)
def generate_srs(
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*EDIT_SRS)),
    llm: LLMProvider = Depends(get_llm),
    db: Session = Depends(get_db),
) -> VersionOut:
    inputs = db.scalars(
        select(RequirementInput).where(RequirementInput.project_id == project.id).order_by(RequirementInput.id)
    ).all()
    text = "\n\n".join(i.content for i in inputs).strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Add requirements on the Input tab before generating an SRS.")
    if len(text) > MAX_INPUT_CHARS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The input is too long for one generation (about 25 pages).")
    if looks_like_injection(text):
        log.warning("project %s: input contains instruction-like text; treated as data only", project.id)

    started = time.monotonic()
    try:
        draft = SRSAgent(llm).run({"text": text})
    except AgentError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    seconds = time.monotonic() - started

    content = {s.number.strip(): s.content.strip() for s in draft.sections}
    sections = [{"number": n, "title": t, "content": content[n]} for n, t in IEEE830_SECTIONS]
    version = create_version(db, project, user, draft.title, sections, assign_ids(draft.requirements), "generated")
    audit.record(db, user, "generate", "srs", version.version_no, project.id, f"{seconds:.1f}s via {llm.name}")
    db.commit()
    return version_out(version)


@router.get("/versions", response_model=list[VersionSummary])
def list_versions(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> list[VersionSummary]:
    query = select(SRSVersion).where(SRSVersion.project_id == project.id).order_by(SRSVersion.version_no.desc())
    return [summary(v) for v in db.scalars(query)]


@router.get("/versions/{version_id}", response_model=VersionOut)
def get_version(version_id: int, project: Project = Depends(get_project), db: Session = Depends(get_db)) -> VersionOut:
    return version_out(load_version(db, project, version_id))


class SectionIn(BaseModel):
    number: str
    content: str = Field(max_length=20_000)


class RequirementIn(BaseModel):
    req_id: str = Field(pattern=r"^[A-Z]{2,4}-\d{1,3}$")
    type: Literal["functional", "non-functional"]
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5_000)
    priority: Literal["Must", "Should", "Could"]


class SaveIn(BaseModel):
    base_version_id: int
    title: str = Field(min_length=1, max_length=200)
    sections: list[SectionIn]
    requirements: list[RequirementIn]
    note: str = Field("", max_length=300)

    @field_validator("requirements")
    @classmethod
    def unique_ids(cls, value: list[RequirementIn]) -> list[RequirementIn]:
        ids = [r.req_id for r in value]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"Duplicate requirement IDs: {', '.join(duplicates)}")
        return value


@router.post("/versions", response_model=VersionOut, status_code=status.HTTP_201_CREATED)
def save_version(
    body: SaveIn,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*EDIT_SRS)),
    db: Session = Depends(get_db),
) -> VersionOut:
    base = load_version(db, project, body.base_version_id)
    edited = {s.number: s.content.strip() for s in body.sections if s.number in SECTION_TITLES}
    # Keep the IEEE 830 order; a section the user removed is kept empty so the completeness check can report it
    sections = [{"number": n, "title": t, "content": edited.get(n, "")} for n, t in IEEE830_SECTIONS]
    version = create_version(
        db, project, user, body.title.strip(), sections, [r.model_dump() for r in body.requirements], "edited",
        body.note.strip() or f"Edited from v{base.version_no}",
    )
    audit.record(db, user, "edit", "srs", version.version_no, project.id, version.note)
    db.commit()
    return version_out(version)


@router.post("/versions/{version_id}/approve", response_model=VersionOut)
def approve_version(
    version_id: int,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*APPROVE_SRS)),
    db: Session = Depends(get_db),
) -> VersionOut:
    version = load_version(db, project, version_id)
    if version.status != "approved":
        version.status = "approved"
        version.approved_by = user.id
        version.approved_at = utcnow()
        audit.record(db, user, "approve", "srs", version.version_no, project.id)
        db.commit()
        db.refresh(version)
    return version_out(version)


class SectionDiff(BaseModel):
    number: str
    title: str
    changed: bool
    lines: list[str]


class RequirementChange(BaseModel):
    req_id: str
    before: RequirementOut | None
    after: RequirementOut | None


class CompareOut(BaseModel):
    a: VersionSummary
    b: VersionSummary
    title_changed: bool
    sections: list[SectionDiff]
    requirements: list[RequirementChange]


@router.get("/compare", response_model=CompareOut)
def compare_versions(
    a: int, b: int, project: Project = Depends(get_project), db: Session = Depends(get_db)
) -> CompareOut:
    old, new = load_version(db, project, a), load_version(db, project, b)
    old_sections = {s["number"]: s for s in old.sections}
    section_diffs = []
    for s in new.sections:
        before = old_sections.get(s["number"], {}).get("content", "").splitlines()
        after = s["content"].splitlines()
        lines = [line for line in difflib.ndiff(before, after) if not line.startswith("?")]
        section_diffs.append(SectionDiff(number=s["number"], title=s["title"], changed=before != after, lines=lines))

    old_reqs = {r.req_id: RequirementOut.model_validate(r) for r in old.requirements}
    new_reqs = {r.req_id: RequirementOut.model_validate(r) for r in new.requirements}
    changes = [
        RequirementChange(req_id=rid, before=old_reqs.get(rid), after=new_reqs.get(rid))
        for rid in sorted(old_reqs.keys() | new_reqs.keys())
        if old_reqs.get(rid) != new_reqs.get(rid)
    ]
    return CompareOut(
        a=summary(old), b=summary(new), title_changed=old.title != new.title, sections=section_diffs,
        requirements=changes,
    )


def latest_approved(db: Session, project: Project) -> SRSVersion | None:
    """The newest approved SRS version: the baseline for tests, test plan and diagrams (SAD AD-5)."""
    query = (
        select(SRSVersion)
        .where(SRSVersion.project_id == project.id, SRSVersion.status == "approved")
        .order_by(SRSVersion.version_no.desc())
    )
    return db.scalars(query).first()


def require_approved(db: Session, project: Project) -> SRSVersion:
    version = latest_approved(db, project)
    if version is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Approve an SRS version first. Generation uses the approved SRS.")
    return version
