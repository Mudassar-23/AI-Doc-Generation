"""
Queue endpoint — shows all jobs and their statuses.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import QueueResponse, QueueItem
from backend.services import queue_service

router = APIRouter()


@router.get("/api/queue", response_model=QueueResponse)
def get_queue(db: Session = Depends(get_db)):
    """Get full queue status — all jobs with positions."""
    status = queue_service.get_queue_status(db)
    all_jobs = queue_service.get_all_jobs(db, limit=50)

    # Calculate queue positions for queued jobs
    queued_jobs = [j for j in all_jobs if j.status == "queued"]
    queued_jobs.sort(key=lambda j: j.created_at)

    items = []
    for job in all_jobs:
        position = None
        if job.status == "queued":
            position = queued_jobs.index(job) + 1

        items.append(QueueItem(
            id=job.id,
            project_name=job.project_name,
            status=job.status,
            queue_position=position,
            created_at=job.created_at,
        ))

    return QueueResponse(
        total_jobs=status["total_jobs"],
        queued=status["queued"],
        running=status["running"],
        completed=status["completed"],
        failed=status["failed"],
        jobs=items,
    )
