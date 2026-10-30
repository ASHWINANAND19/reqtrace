"""Password hashing (SEC-01) and signed session tokens (SEC-02)."""
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import get_settings

ALGORITHM = "HS256"
# Hard upper bound on a token's life; inactivity expiry (60 min) is enforced server-side.
MAX_TOKEN_HOURS = 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def new_jti() -> str:
    return uuid.uuid4().hex


def create_token(user_id: int, jti: str) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "jti": jti, "iat": now, "exp": now + timedelta(hours=MAX_TOKEN_HOURS)}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError if the token is invalid, tampered with or past its hard expiry."""
    return jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
