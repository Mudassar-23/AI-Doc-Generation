"""
Queue service — queue position calculation and status.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from backend.models import Job


def get_queue_position(db: Session, job_id: int) -> int:
    """
    Get the queue position of a job.
    Position 0 = currently running.
    Position 1 = next in line.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or job.status != "queued":
        return 0

    # Count jobs that are queued and were created before this one
    position = (
        db.query(func.count(Job.id))
        .filter(Job.status == "queued")
        .filter(Job.created_at < job.created_at)
        .scalar()
    )
    return position + 1  # 1-indexed


def get_queue_status(db: Session) -> dict:
    """Get full queue status summary."""
    total = db.query(func.count(Job.id)).scalar() or 0
    queued = db.query(func.count(Job.id)).filter(Job.status == "queued").scalar() or 0
    running = db.query(func.count(Job.id)).filter(Job.status == "running").scalar() or 0
    completed = db.query(func.count(Job.id)).filter(Job.status == "completed").scalar() or 0
    failed = db.query(func.count(Job.id)).filter(Job.status == "failed").scalar() or 0

    return {
        "total_jobs": total,
        "queued": queued,
        "running": running,
        "completed": completed,
        "failed": failed,
    }


def get_all_jobs(db: Session, limit: int = 50) -> List[Job]:
    """Get all jobs ordered by creation time (newest first)."""
    return (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .all()
    )


def get_queued_jobs(db: Session) -> List[Job]:
    """Get all queued jobs in FIFO order."""
    return (
        db.query(Job)
        .filter(Job.status == "queued")
        .order_by(Job.created_at.asc())
        .all()
    )
