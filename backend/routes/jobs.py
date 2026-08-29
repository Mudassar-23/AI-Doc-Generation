"""
Job endpoints — submit, status, progress, download, retry.
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware.rate_limit import check_rate_limit
from backend.schemas import (
    JobCreateRequest, JobCreateResponse, JobResponse,
    JobProgressResponse, ProgressStage, JobRetryRequest,
    JobLogsResponse, LogEntry,
)
from backend.services import job_service, queue_service

router = APIRouter()


import re

@router.post("/api/jobs", response_model=JobCreateResponse, status_code=201, dependencies=[Depends(check_rate_limit)])
def create_job(request: JobCreateRequest, db: Session = Depends(get_db)):

    """Submit a new documentation generation job."""
    job = job_service.create_job(
        db=db,
        project_name=request.project_name,
        repo_url=request.repo_url,
        source_type=request.source_type,
        ai_provider=request.ai_provider,
        pat_token=request.pat_token,
    )

    position = queue_service.get_queue_position(db, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        queue_position=position,
        message=f"Job queued at position {position}",
    )


@router.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job details and status."""
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    sanitized_url = re.sub(r'https?://([^@]+)@', 'https://', job.repo_url)
    resp = JobResponse.model_validate(job)
    resp.repo_url = sanitized_url
    return resp


@router.get("/api/jobs/{job_id}/progress", response_model=JobProgressResponse)
def get_job_progress(job_id: int, db: Session = Depends(get_db)):
    """Get real-time progress for a job."""
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress_entries = job_service.get_job_progress(db, job_id)

    # Define all pipeline stages
    all_stages = [
        "cloning", "analyzing", "chunking", "llm_analysis",
        "context_building", "template_filling", "packaging"
    ]

    # Map progress entries to stages
    progress_map = {p.stage: p for p in progress_entries}
    stages = []
    current_stage = None
    overall_percent = 0

    for stage_name in all_stages:
        if stage_name in progress_map:
            p = progress_map[stage_name]
            stages.append(ProgressStage(
                stage=stage_name,
                percent=p.percent,
                message=p.message,
                updated_at=p.updated_at,
            ))
            if p.percent < 100:
                current_stage = stage_name
        else:
            stages.append(ProgressStage(
                stage=stage_name,
                percent=0,
                message=None,
            ))

    # Calculate overall percent
    if stages:
        overall_percent = sum(s.percent for s in stages) // len(stages)

    # Determine current stage
    if not current_stage and job.status == "running":
        for s in stages:
            if s.percent < 100:
                current_stage = s.stage
                break

    # Build current message
    message = None
    if current_stage and current_stage in progress_map:
        message = progress_map[current_stage].message

    return JobProgressResponse(
        job_id=job_id,
        status=job.status,
        stages=stages,
        overall_percent=overall_percent,
        current_stage=current_stage,
        message=message,
    )


@router.get("/api/jobs/{job_id}/download")
def download_job(job_id: int, db: Session = Depends(get_db)):
    """Download the generated ZIP file."""
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.zip_generated or not job.zip_path:
        raise HTTPException(status_code=404, detail="ZIP not ready yet")
    if not os.path.exists(job.zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found on disk")

    filename = f"{job.project_name.replace(' ', '-')}-docs.zip"
    return FileResponse(
        path=job.zip_path,
        filename=filename,
        media_type="application/zip",
    )


@router.post("/api/jobs/{job_id}/retry", response_model=JobResponse, dependencies=[Depends(check_rate_limit)])
def retry_job(job_id: int, db: Session = Depends(get_db)):

    """Retry a failed job."""
    job = job_service.retry_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=400,
            detail="Job not found or not in failed state"
        )
    return job


@router.get("/api/jobs/{job_id}/logs", response_model=JobLogsResponse)
def get_job_logs(job_id: int, db: Session = Depends(get_db)):
    """Get job logs."""
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs = job_service.get_job_logs(db, job_id)
    return JobLogsResponse(
        job_id=job_id,
        logs=[LogEntry(level=l.level, message=l.message, created_at=l.created_at) for l in logs],
    )
