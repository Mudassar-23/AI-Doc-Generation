"""
Database initialization script.
Creates tables in PostgreSQL if available, falls back to SQLite.
"""
import os
import sys

# Add parent directory to path so we can import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Boolean, Text,
    DateTime, ForeignKey, text
)
from sqlalchemy.sql import func
from datetime import datetime


def get_engine():
    """Try PostgreSQL first, fall back to SQLite."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

    pg_url = os.getenv("DATABASE_URL", "")
    sqlite_url = os.getenv("DATABASE_FALLBACK_URL", "sqlite:///./data/aidocs.db")

    if pg_url:
        try:
            engine = create_engine(pg_url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[DB] Connection to PostgreSQL successful")
            return engine, "postgresql"
        except Exception as e:
            print(f"[DB] PostgreSQL connection failed, falling back to SQLite")

    # Ensure SQLite directory exists
    if sqlite_url.startswith("sqlite:///"):
        db_path = sqlite_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    engine = create_engine(sqlite_url)
    print(f"[DB] Using SQLite: {sqlite_url}")
    return engine, "sqlite"


def create_tables(engine, db_type):
    """Create all tables."""
    metadata = MetaData()

    # ---- jobs ----
    jobs = Table(
        "jobs", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("project_name", String(255), nullable=False),
        Column("repo_url", String(2048), nullable=False),
        Column("source_type", String(20), nullable=False),        # github | azure_devops
        Column("ai_provider", String(20), nullable=False),        # abacus | azure_ai | mock
        Column("status", String(20), nullable=False, default="queued"),  # queued | running | completed | failed
        Column("zip_generated", Boolean, nullable=False, default=False),
        Column("zip_path", String(512), nullable=True),
        Column("error_message", Text, nullable=True),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column("completed_at", DateTime, nullable=True),
    )

    # ---- job_progress ----
    job_progress = Table(
        "job_progress", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("job_id", Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        Column("stage", String(50), nullable=False),
        Column("percent", Integer, default=0),
        Column("message", Text, nullable=True),
        Column("updated_at", DateTime, default=datetime.utcnow),
    )

    # ---- job_logs ----
    job_logs = Table(
        "job_logs", metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("job_id", Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        Column("level", String(10), nullable=False),  # info | warn | error | debug
        Column("message", Text, nullable=False),
        Column("created_at", DateTime, default=datetime.utcnow),
    )

    metadata.create_all(engine)
    print("[DB] All tables created successfully")
    print("     - jobs")
    print("     - job_progress")
    print("     - job_logs")


if __name__ == "__main__":
    engine, db_type = get_engine()
    create_tables(engine, db_type)
    print(f"\n[DB] Database initialization complete ({db_type})")
