"""Request dependencies: authentication, role checks and project membership (SEC-02, SEC-03, SEC-07)."""
from collections.abc import Callable
from datetime import timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db, utcnow
from app.models import AuthSession, Project, ProjectMember, User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, message, headers={"WWW-Authenticate": "Bearer"})


def get_current_session(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> AuthSession:
    if creds is None:
        raise _unauthorized("Please log in.")
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError as exc:
        raise _unauthorized("Your session is invalid or has expired. Please log in again.") from exc

    session = db.get(AuthSession, payload.get("jti", ""))
    if session is None or session.revoked:
        raise _unauthorized("Your session has ended. Please log in again.")

    now = utcnow()
    if now - session.last_seen > timedelta(minutes=get_settings().session_minutes):
        session.revoked = True
        db.commit()
        raise _unauthorized("Your session expired after inactivity. Please log in again.")

    if not session.user.is_active:
        raise _unauthorized("This account is disabled.")

    session.last_seen = now
    db.commit()
    return session


def get_current_user(session: AuthSession = Depends(get_current_session)) -> User:
    return session.user


def require_roles(*roles: str) -> Callable[..., User]:
    """Dependency factory: allow only the given roles, otherwise HTTP 403 (FR-12)."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Your role ({user.role}) is not allowed to do this."
            )
        return user

    return checker


def get_project(project_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Project:
    """Load a project the current user is a member of (SEC-07)."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    if db.get(ProjectMember, (project_id, user.id)) is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a member of this project.")
    return project
