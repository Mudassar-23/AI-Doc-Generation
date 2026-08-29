"""
Job service — business logic for job creation, status, and retry.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from backend.models import Job, JobProgress, JobLog


import re
from backend.config import get_settings


def clean_pat_token(pat_token: str) -> str:
    """Clean PAT token input by removing prefixes like token=, pat=, quotes, or whitespace."""
    if not pat_token:
        return ""
    pat = pat_token.strip().strip("'\"")
    pat = re.sub(r'^(token|pat|bearer)[:=]\s*', '', pat, flags=re.IGNORECASE).strip()
    return pat


def normalize_repo_url(repo_url: str, source_type: str = "github") -> str:
    """Ensure Azure DevOps URLs are complete using ADO_ORGANIZATION_URL if needed."""
    url = repo_url.strip()
    settings = get_settings()

    is_azure = (
        source_type in ("azure_devops", "azure")
        or "dev.azure.com" in url
        or "visualstudio.com" in url
        or "_git" in url
    )

    if is_azure:
        if not url.startswith("http://") and not url.startswith("https://"):
            org_base = (settings.ado_organization_url or "https://dev.azure.com").rstrip("/")
            if not org_base.startswith("http://") and not org_base.startswith("https://"):
                org_base = f"https://{org_base}"
            url = f"{org_base}/{url.lstrip('/')}"

    return url


def format_authed_url(repo_url: str, pat_token: Optional[str] = None, source_type: str = "github") -> str:
    """Format repository URL with PAT token for authentication, falling back to .env settings if empty."""
    settings = get_settings()
    repo_url = normalize_repo_url(repo_url, source_type)

    token = clean_pat_token(pat_token) if pat_token else ""

    is_azure = (
        source_type in ("azure_devops", "azure")
        or "dev.azure.com" in repo_url
        or "visualstudio.com" in repo_url
    )

    # Fall back to env credentials if no PAT was provided in the UI request
    if not token:
        if is_azure and settings.ado_pat:
            token = clean_pat_token(settings.ado_pat)
        elif not is_azure and settings.github_pat:
            token = clean_pat_token(settings.github_pat)

    if not token:
        return repo_url

    # If URL already has inline credentials, keep as is
    if "@" in repo_url.split("://")[-1]:
        return repo_url

    if "github.com" in repo_url:
        if repo_url.startswith("https://"):
            return f"https://x-access-token:{token}@{repo_url[8:]}"
        elif repo_url.startswith("http://"):
            return f"http://x-access-token:{token}@{repo_url[7:]}"
    else:
        # Azure DevOps & generic git repositories
        if repo_url.startswith("https://"):
            return f"https://{token}@{repo_url[8:]}"
        elif repo_url.startswith("http://"):
            return f"http://{token}@{repo_url[7:]}"

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
    settings = get_settings()
    if not ai_provider or ai_provider.lower() in ("default", ""):
        ai_provider = settings.default_ai_provider

    authed_url = format_authed_url(repo_url, pat_token, source_type=source_type)
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
