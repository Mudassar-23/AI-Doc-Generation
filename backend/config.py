"""
Backend configuration — loads settings from .env file and secret manager/docker secrets.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional, List
from dotenv import load_dotenv

# Load .env from project root so that get_secret() / os.getenv() calls in
# class-level defaults find the values before pydantic_settings.__init__ runs.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))



def get_secret(secret_name: str, default: str = "") -> str:
    """
    Fetch secret value with fallback sequence:
    1. Environment variable
    2. Docker / K8s file secret (/run/secrets/<secret_name>)
    3. Default fallback value
    """
    val = os.getenv(secret_name)
    if val:
        return val

    # Check Docker / K8s secret file location
    secret_path = f"/run/secrets/{secret_name.lower()}"
    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            pass

    return default


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file / secret manager."""

    # Database
    database_url: str = get_secret("DATABASE_URL", "postgresql://aidocs:password@localhost:5432/aidocs")
    database_fallback_url: str = get_secret("DATABASE_FALLBACK_URL", "sqlite:///./data/aidocs.db")

    # Abacus AI
    abacus_api_key: str = get_secret("ABACUS_API_KEY", "")
    abacus_deployment_token: str = get_secret("ABACUS_DEPLOYMENT_TOKEN", "")
    abacus_model: str = os.getenv("ABACUS_MODEL", "claude-sonnet")

    # Azure AI Foundry
    azure_ai_endpoint: str = get_secret("AZURE_AI_ENDPOINT", "")
    azure_ai_api_key: str = get_secret("AZURE_AI_API_KEY", "")
    azure_ai_deployment_name: str = os.getenv("AZURE_AI_DEPLOYMENT_NAME", "")
    azure_ai_api_version: str = os.getenv("AZURE_AI_API_VERSION", "2024-06-01")

    # Azure DevOps / GitHub Credentials
    ado_pat: str = get_secret("ADO_PAT", get_secret("AZURE_DEVOPS_PAT", ""))
    ado_organization_url: str = os.getenv("ADO_ORGANIZATION_URL", os.getenv("AZURE_DEVOPS_ORG_URL", ""))
    github_pat: str = get_secret("GITHUB_PAT", "")

    # Default AI Provider
    default_ai_provider: str = os.getenv("DEFAULT_AI_PROVIDER", "azure_ai")

    # Security & CORS
    allowed_cors_origins: str = os.getenv("ALLOWED_CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

    # Runner
    runner_poll_interval: int = int(os.getenv("RUNNER_POLL_INTERVAL", "2"))
    max_job_duration_minutes: int = int(os.getenv("MAX_JOB_DURATION_MINUTES", "30"))

    # Output
    output_dir: str = os.getenv("OUTPUT_DIR", "./outputs")
    temp_dir: str = os.getenv("TEMP_DIR", "./tmp")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    @property
    def allowed_origins_list(self) -> List[str]:
        if not self.allowed_cors_origins or self.allowed_cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_cors_origins.split(",") if origin.strip()]

    # Azure OpenAI Embeddings
    azure_embedding_endpoint: str = os.getenv("AZURE_EMBEDDING_ENDPOINT", "")
    azure_embedding_deployment: str = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

