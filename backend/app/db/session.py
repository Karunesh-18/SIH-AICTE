from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(conn, _):
    if settings.database_url.startswith("sqlite"):
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """One session per request; use cases commit via uow()."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def uow(db: Session) -> Iterator[Session]:
    """Unit of Work: state change + audit + outbox commit or roll back together (D-04)."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
