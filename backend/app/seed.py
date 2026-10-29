"""Create the initial Administrator from ADMIN_EMAIL / ADMIN_PASSWORD (admins cannot self-register)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Role, User
from app.security import hash_password


def seed_admin(db: Session) -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    email = settings.admin_email.lower()
    if db.scalar(select(User).where(User.email == email)):
        return
    db.add(User(name="Administrator", email=email, password_hash=hash_password(settings.admin_password),
                role=Role.ADMIN))
    db.commit()
