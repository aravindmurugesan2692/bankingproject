"""SQLAlchemy engine and session — SQLite now, Postgres-ready via DATABASE_URL."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    """Add Phase 8 Incident columns on existing SQLite files (create_all won't alter)."""
    if not settings.database_url.startswith("sqlite"):
        return
    needed = {
        "restored_at": "DATETIME",
        "closed_at": "DATETIME",
        "rca_status": "VARCHAR(64)",
    }
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(incidents)").fetchall()
        existing = {r[1] for r in rows}
        for col, col_type in needed.items():
            if col not in existing:
                conn.exec_driver_sql(
                    f"ALTER TABLE incidents ADD COLUMN {col} {col_type}"
                )
