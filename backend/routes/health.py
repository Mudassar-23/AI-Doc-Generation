"""
Health and provider endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db, get_db_type
from backend.models import Job
from backend.config import get_settings
from backend.schemas import HealthResponse, ProvidersResponse, ProviderInfo

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    settings = get_settings()
    db_type = get_db_type()

    queue_depth = db.query(func.count(Job.id)).filter(Job.status == "queued").scalar() or 0
    total_jobs = db.query(func.count(Job.id)).scalar() or 0

    return HealthResponse(
        status="healthy",
        database="connected",
        database_type=db_type,
        queue_depth=queue_depth,
        total_jobs=total_jobs,
    )


@router.get("/api/providers", response_model=ProvidersResponse)
def list_providers():
    """List available AI providers."""
    settings = get_settings()

    providers = [
        ProviderInfo(
            name="abacus",
            display_name="Abacus AI (Claude Sonnet)",
            available=bool(settings.abacus_api_key),
            model=settings.abacus_model,
        ),
        ProviderInfo(
            name="azure_ai",
            display_name="Azure AI Foundry",
            available=bool(settings.azure_ai_api_key),
            model=settings.azure_ai_deployment_name or None,
        ),
        ProviderInfo(
            name="mock",
            display_name="Mock Mode (Testing)",
            available=True,
            model="mock-v1",
        ),
    ]

    return ProvidersResponse(
        providers=providers,
        default=settings.default_ai_provider,
    )
