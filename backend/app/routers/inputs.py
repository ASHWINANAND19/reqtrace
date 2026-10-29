"""Raw requirements input: typed text and uploaded files (FR-03, SEC-04)."""
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.config import get_settings
from app.db import get_db
from app.deps import get_project, require_roles
from app.models import Project, RequirementInput, User
from app.parsing import FileTooLargeError, UnsupportedFileError, clean_text, extract_text, safe_filename
from app.permissions import MANAGE_INPUT

router = APIRouter(prefix="/api/projects/{project_id}/inputs", tags=["inputs"])


class TextIn(BaseModel):
    content: str = Field(max_length=200_000)

    @field_validator("content")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = clean_text(value)
        if not value:
            raise ValueError("Requirements text cannot be empty")
        return value


class InputOut(BaseModel):
    id: int
    kind: str
    filename: str | None
    content: str
    author_name: str | None
    created_at: datetime


def _out(item: RequirementInput) -> InputOut:
    return InputOut(
        id=item.id,
        kind=item.kind,
        filename=item.filename,
        content=item.content,
        author_name=item.author.name if item.author else None,
        created_at=item.created_at,
    )


@router.get("", response_model=list[InputOut])
def list_inputs(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> list[InputOut]:
    query = select(RequirementInput).where(RequirementInput.project_id == project.id).order_by(RequirementInput.id)
    return [_out(i) for i in db.scalars(query)]


@router.post("/text", response_model=InputOut, status_code=status.HTTP_201_CREATED)
def add_text(
    body: TextIn,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*MANAGE_INPUT)),
    db: Session = Depends(get_db),
) -> InputOut:
    item = RequirementInput(project_id=project.id, kind="text", content=body.content, created_by=user.id)
    db.add(item)
    db.flush()
    audit.record(db, user, "create", "input", item.id, project.id, "typed text")
    db.commit()
    return _out(item)


@router.post("/file", response_model=InputOut, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...),
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*MANAGE_INPUT)),
    db: Session = Depends(get_db),
) -> InputOut:
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    filename = safe_filename(file.filename or "upload")
    data = file.file.read(max_bytes + 1)  # read one byte past the limit to detect oversize files
    try:
        text = extract_text(filename, data, max_bytes)
    except FileTooLargeError as exc:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, str(exc)) from exc
    except UnsupportedFileError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc

    folder = Path(settings.storage_dir) / "uploads" / str(project.id)
    folder.mkdir(parents=True, exist_ok=True)
    stored = folder / f"{uuid.uuid4().hex}{Path(filename).suffix.lower()}"
    stored.write_bytes(data)

    item = RequirementInput(
        project_id=project.id, kind="file", filename=filename, stored_path=str(stored), content=text,
        created_by=user.id,
    )
    db.add(item)
    db.flush()
    audit.record(db, user, "create", "input", item.id, project.id, filename)
    db.commit()
    return _out(item)


@router.delete("/{input_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_input(
    input_id: int,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*MANAGE_INPUT)),
    db: Session = Depends(get_db),
) -> Response:
    item = db.get(RequirementInput, input_id)
    if item is None or item.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Input not found.")
    audit.record(db, user, "delete", "input", item.id, project.id, item.filename or "typed text")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
