import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


def get_resolved_database_url() -> str:
    """
    Resolve DATABASE_URL cleanly.
    - If using SQLite with a relative path (e.g. sqlite:///./data/attendance.db),
      resolve it stably relative to the backend root directory for offline/local use.
    - If using Oracle Cloud MySQL HeatWave / MySQL (mysql+pymysql://...), return directly.
    - If using PostgreSQL or other databases, return directly.
    """
    url = settings.DATABASE_URL.strip()
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
    elif url.startswith("mysql://"):
        # Auto-upgrade mysql:// to mysql+pymysql:// for PyMySQL driver
        return url.replace("mysql://", "mysql+pymysql://", 1)
    return url


RESOLVED_DATABASE_URL = get_resolved_database_url()
is_sqlite = RESOLVED_DATABASE_URL.startswith("sqlite")
is_mysql = RESOLVED_DATABASE_URL.startswith("mysql")

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

elif is_mysql:
    # Central Production Database: Oracle Cloud MySQL HeatWave / MySQL
    engine = create_engine(
        RESOLVED_DATABASE_URL,
        connect_args={
        "ssl": {
            "ca": "/path/to/ca.pem"
        }
    },
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
        pool_timeout=30,
        echo=False
    )

else:
    # PostgreSQL / Other
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
