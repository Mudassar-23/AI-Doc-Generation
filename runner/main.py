"""
Runner Entry Point — polls the database for queued jobs and processes them one at a time (FIFO).

This is the single runner process. It:
  1. Polls the database every N seconds for the oldest queued job
  2. Claims the job (sets status to 'running')
  3. Runs the 7-stage pipeline via StageManager
  4. On completion, automatically picks the next queued job
  5. Handles graceful shutdown on SIGTERM/SIGINT
"""
import sys
import os
import time
import signal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from runner.config import RunnerConfig
from runner.stage_manager import StageManager
from runner.providers.mock_provider import MockProvider
from runner.providers.abacus_provider import AbacusProvider
from runner.providers.azure_ai_provider import AzureAIProvider

# Import models after path setup
from backend.models import Base, Job


import threading

# Global shutdown flag
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    print("\n[Runner] Shutdown requested — finishing current job...")
    _shutdown_requested = True


def get_engine():
    """Connect to database — PostgreSQL first, fallback to SQLite."""
    pg_url = RunnerConfig.DATABASE_URL
    sqlite_url = RunnerConfig.DATABASE_FALLBACK_URL

    if pg_url:
        try:
            engine = create_engine(pg_url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[Runner DB] Connected to PostgreSQL")
            return engine
        except Exception as e:
            print(f"[Runner DB] PostgreSQL unavailable, falling back to SQLite")

    # SQLite fallback
    if sqlite_url.startswith("sqlite:///"):
        db_path = sqlite_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False} if "sqlite" in sqlite_url else {},
    )
    print(f"[Runner DB] Using SQLite: {sqlite_url}")

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    return engine


from runner.providers import FallbackProvider


def get_provider(provider_name: str):
    """Create an AI provider instance with runtime fallback sequence (Abacus -> Azure AI -> Mock)."""
    return FallbackProvider(provider_name)


def claim_next_job(session) -> Job:
    """Claim the next queued job (FIFO — oldest first)."""
    job = (
        session.query(Job)
        .filter(Job.status == "queued")
        .order_by(Job.created_at.asc())
        .first()
    )
    return job


def main():
    """Main runner loop."""
    global _shutdown_requested

    # Setup signal handlers if main thread
    if threading.current_thread() is threading.main_thread():
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except (ValueError, AttributeError):
            pass

    print("=" * 60)
    print("  AI Docs Generator — Runner")
    print(f"  Poll interval: {RunnerConfig.POLL_INTERVAL}s")
    print(f"  Default provider: {RunnerConfig.DEFAULT_AI_PROVIDER}")
    print("=" * 60)

    # Connect to database
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)

    # Ensure output and temp directories exist
    os.makedirs(RunnerConfig.OUTPUT_DIR, exist_ok=True)
    os.makedirs(RunnerConfig.TEMP_DIR, exist_ok=True)

    print("[Runner] Ready — polling for jobs...\n")

    while not _shutdown_requested:
        session = SessionLocal()
        try:
            # Look for the next queued job
            job = claim_next_job(session)

            if job:
                print(f"\n[Runner] Job #{job.id}: '{job.project_name}'")
                print(f"         Repo: {job.repo_url}")
                print(f"         Provider: {job.ai_provider}")

                # Get the AI provider
                provider = get_provider(job.ai_provider)
                print(f"         Using: {provider.get_provider_name()}")

                # Run the pipeline
                manager = StageManager(db=session, provider=provider)
                manager.run_job(job)

                # Check result
                session.refresh(job)
                if job.status == "completed":
                    print(f"[Runner] Job #{job.id} completed — ZIP: {job.zip_path}")
                else:
                    print(f"[Runner] Job #{job.id} failed — {job.error_message}")

                print(f"[Runner] Job #{job.id} done\n")

                # Immediately check for next job (don't wait)
                continue

            else:
                # No jobs — wait before polling again
                time.sleep(RunnerConfig.POLL_INTERVAL)

        except Exception as e:
            print(f"[Runner] Error in main loop: {e}")
            time.sleep(RunnerConfig.POLL_INTERVAL)
        finally:
            session.close()

    print("[Runner] Shutdown complete")


if __name__ == "__main__":
    main()
