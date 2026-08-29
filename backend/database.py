"""
Database connection — PostgreSQL with automatic SQLite fallback.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from backend.config import get_settings

_engine = None
_SessionLocal = None
_db_type = None


def init_database():
    """Initialize database connection. Try PostgreSQL first, fall back to SQLite."""
    global _engine, _SessionLocal, _db_type
    settings = get_settings()

    # Try PostgreSQL
    if settings.database_url:
        try:
            engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _engine = engine
            _db_type = "postgresql"
            print("[DB] Connected to PostgreSQL")
        except Exception as e:
            print("[DB] PostgreSQL unavailable, falling back to SQLite")

    # Fall back to SQLite
    if _engine is None:
        sqlite_url = settings.database_fallback_url
        if sqlite_url.startswith("sqlite:///"):
            db_path = sqlite_url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

        _engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False} if "sqlite" in sqlite_url else {},
        )
        _db_type = "sqlite"
        print(f"[DB] Using SQLite: {sqlite_url}")

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    # Create tables
    from backend.models import Base
    Base.metadata.create_all(bind=_engine)
    print("[DB] Tables created/verified")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a database session."""
    if _SessionLocal is None:
        init_database()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """Get the SQLAlchemy engine."""
    if _engine is None:
        init_database()
    return _engine


def get_db_type() -> str:
    """Get current database type ('postgresql' or 'sqlite')."""
    if _db_type is None:
        init_database()
    return _db_type
