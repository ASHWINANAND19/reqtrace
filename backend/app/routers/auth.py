"""Registration, login and logout (FR-01, SEC-01, SEC-02)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.db import get_db
from app.deps import get_current_session, get_current_user
from app.models import AuthSession, Role, User
from app.security import create_token, hash_password, new_jti, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

SELF_SERVICE_ROLES = (Role.ANALYST, Role.QA, Role.DEVELOPER)


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    # bcrypt only uses the first 72 bytes, so longer passwords are refused rather than truncated
    password: str = Field(min_length=8, max_length=72)
    role: Role = Role.ANALYST

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> User:
    if body.role not in SELF_SERVICE_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator accounts are assigned by an admin.")
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = User(name=body.name, email=email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.flush()
    audit.record(db, user, "register", "user", user.id)
    db.commit()
    return user


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash) or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
    jti = new_jti()
    db.add(AuthSession(jti=jti, user_id=user.id))
    db.commit()
    return TokenOut(access_token=create_token(user.id, jti), user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)) -> Response:
    session.revoked = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
