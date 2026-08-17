import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


def get_resolved_database_url() -> str:
    """
    Resolve DATABASE_URL cleanly.
    If using SQLite with a relative path (e.g. sqlite:///./data/attendance.db),
    resolve it stably relative to the backend root directory so that working directory
    differences between local development and Render production never create disconnected DB files.
    """
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///./") or url.startswith("sqlite:///.\\"):
        rel_path = url.split("sqlite:///", 1)[1]  # e.g. './data/attendance.db'
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        abs_db_path = os.path.abspath(os.path.join(backend_dir, rel_path))
        os.makedirs(os.path.dirname(abs_db_path), exist_ok=True)
        norm_path = abs_db_path.replace("\\", "/")
        return f"sqlite:///{norm_path}"
    elif url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return url
    return url


RESOLVED_DATABASE_URL = get_resolved_database_url()
is_sqlite = RESOLVED_DATABASE_URL.startswith("sqlite")

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        RESOLVED_DATABASE_URL,
        connect_args=connect_args,
        echo=False
    )

    # Enable foreign keys and WAL mode for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

else:
    # MySQL / PostgreSQL configuration
    engine = create_engine(
        RESOLVED_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
