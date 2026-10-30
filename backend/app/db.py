"""Database engine, session factory and table creation."""
from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite and PostgreSQL compare consistently)."""
    return datetime.now(UTC).replace(tzinfo=None)


def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


def make_engine(url: str):
    if not url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True)
    kwargs: dict = {"connect_args": {"check_same_thread": False}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool
    sqlite_engine = create_engine(url, **kwargs)
    event.listen(sqlite_engine, "connect", _enable_sqlite_foreign_keys)
    return sqlite_engine


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (registers tables)

    with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            # Several back-end replicas may start together (Kubernetes); only one creates the tables
            conn.execute(text("SELECT pg_advisory_xact_lock(4242)"))
        Base.metadata.create_all(conn)
