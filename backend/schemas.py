"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== Request Schemas ====================

class JobCreateRequest(BaseModel):
    """Request to submit a new documentation generation job."""
    project_name: str = Field(..., min_length=1, max_length=255, description="Name of the project")
    repo_url: str = Field(..., min_length=10, max_length=2048, description="Repository URL")
    pat_token: Optional[str] = Field(default=None, description="Optional Personal Access Token for repository authentication")
    source_type: str = Field(..., pattern="^(github|azure_devops)$", description="Source type")
    ai_provider: str = Field(default="mock", pattern="^(abacus|azure_ai|mock)$", description="AI provider")


class JobRetryRequest(BaseModel):
    """Request to retry a failed job."""
    pass  # No body needed — just POST to the endpoint


# ==================== Response Schemas ====================

class JobResponse(BaseModel):
    """Job details response."""
    id: int
    project_name: str
    repo_url: str
    source_type: str
    ai_provider: str
    status: str
    zip_generated: bool
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobCreateResponse(BaseModel):
    """Response after creating a new job."""
    job_id: int
    status: str
    queue_position: int
    message: str


class ProgressStage(BaseModel):
    """Progress for a single pipeline stage."""
    stage: str
    percent: int
    message: Optional[str] = None
    updated_at: Optional[datetime] = None


class JobProgressResponse(BaseModel):
    """Real-time progress response."""
    job_id: int
    status: str
    stages: List[ProgressStage]
    overall_percent: int
    current_stage: Optional[str] = None
    message: Optional[str] = None


class QueueItem(BaseModel):
    """A single item in the queue."""
    id: int
    project_name: str
    status: str
    queue_position: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QueueResponse(BaseModel):
    """Full queue status."""
    total_jobs: int
    queued: int
    running: int
    completed: int
    failed: int
    jobs: List[QueueItem]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    database_type: str
    queue_depth: int
    total_jobs: int


class ProviderInfo(BaseModel):
    """AI provider information."""
    name: str
    display_name: str
    available: bool
    model: Optional[str] = None


class ProvidersResponse(BaseModel):
    """Available AI providers."""
    providers: List[ProviderInfo]
    default: str


class LogEntry(BaseModel):
    """A single log entry."""
    level: str
    message: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobLogsResponse(BaseModel):
    """Job logs response."""
    job_id: int
    logs: List[LogEntry]
