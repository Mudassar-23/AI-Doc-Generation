"""
Job service — business logic for job creation, status, and retry.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from backend.models import Job, JobProgress, JobLog


import re


def clean_pat_token(pat_token: str) -> str:
    """Clean PAT token input by removing prefixes like token=, pat=, quotes, or whitespace."""
    if not pat_token:
        return ""
    pat = pat_token.strip().strip("'\"")
    pat = re.sub(r'^(token|pat|bearer)[:=]\s*', '', pat, flags=re.IGNORECASE).strip()
    return pat


def format_authed_url(repo_url: str, pat_token: Optional[str]) -> str:
    """Format repository URL with PAT token for authentication if provided."""
    if not pat_token or not pat_token.strip():
        return repo_url
    pat = clean_pat_token(pat_token)
    if not pat:
        return repo_url
    if "@" in repo_url.split("://")[-1]:
        return repo_url

    if "github.com" in repo_url:
        # Use x-access-token for GitHub PATs (supports both fine-grained github_pat_ and classic ghp_ tokens)
        if repo_url.startswith("https://"):
            return f"https://x-access-token:{pat}@{repo_url[8:]}"
        elif repo_url.startswith("http://"):
            return f"http://x-access-token:{pat}@{repo_url[7:]}"
    else:
        if repo_url.startswith("https://"):
            return f"https://{pat}@{repo_url[8:]}"
        elif repo_url.startswith("http://"):
            return f"http://{pat}@{repo_url[7:]}"
    return repo_url


def create_job(
    db: Session,
    project_name: str,
    repo_url: str,
    source_type: str,
    ai_provider: str,
    pat_token: Optional[str] = None,
) -> Job:
    """Create a new documentation generation job."""
    authed_url = format_authed_url(repo_url, pat_token)
    job = Job(
        project_name=project_name,
        repo_url=authed_url,
        source_type=source_type,
        ai_provider=ai_provider,
        status="queued",
        zip_generated=False,
        created_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Add initial log entry (sanitize URL for log)
    sanitized_log_url = repo_url  # Keep log clean without exposing PAT
    log = JobLog(
        job_id=job.id,
        level="info",
        message=f"Job created — project: {project_name}, provider: {ai_provider}, repo: {sanitized_log_url}",
        created_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()

    return job


def get_job(db: Session, job_id: int) -> Optional[Job]:
    """Get a job by ID."""
    return db.query(Job).filter(Job.id == job_id).first()


def get_job_progress(db: Session, job_id: int) -> List[JobProgress]:
    """Get all progress entries for a job."""
    return (
        db.query(JobProgress)
        .filter(JobProgress.job_id == job_id)
        .order_by(JobProgress.updated_at.asc())
        .all()
    )


def get_job_logs(db: Session, job_id: int) -> List[JobLog]:
    """Get all log entries for a job."""
    return (
        db.query(JobLog)
        .filter(JobLog.job_id == job_id)
        .order_by(JobLog.created_at.asc())
        .all()
    )


def retry_job(db: Session, job_id: int) -> Optional[Job]:
    """Retry a failed job by re-queuing it."""
    job = get_job(db, job_id)
    if not job:
        return None
    if job.status != "failed":
        return None

    job.status = "queued"
    job.error_message = None
    job.zip_generated = False
    job.zip_path = None
    job.completed_at = None
    job.created_at = datetime.utcnow()  # Re-queue at end of line

    # Log the retry
    log = JobLog(
        job_id=job.id,
        level="info",
        message="Job retried — re-queued for processing",
        created_at=datetime.utcnow(),
    )
    db.add(log)

    # Clear old progress
    db.query(JobProgress).filter(JobProgress.job_id == job_id).delete()

    db.commit()
    db.refresh(job)
    return job


def cancel_job(db: Session, job_id: int) -> Optional[Job]:
    """Cancel a queued job."""
    job = get_job(db, job_id)
    if not job:
        return None
    if job.status not in ("queued",):
        return None

    job.status = "failed"
    job.error_message = "Cancelled by user"

    log = JobLog(
        job_id=job.id,
        level="info",
        message="Job cancelled by user",
        created_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(job)
    return job
