"""
SQLAlchemy ORM models — simplified schema.
Tables: jobs, job_progress, job_logs
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Job(Base):
    """
    Core jobs table.
    Tracks: id, repo_url, status (queued/running/completed/failed), zip_generated (yes/no).
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255), nullable=False)
    repo_url = Column(String(2048), nullable=False)
    source_type = Column(String(20), nullable=False)       # github | azure_devops
    ai_provider = Column(String(20), nullable=False)       # abacus | azure_ai | mock
    status = Column(String(20), nullable=False, default="queued")  # queued | running | completed | failed
    zip_generated = Column(Boolean, nullable=False, default=False)
    zip_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    progress = relationship("JobProgress", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, project='{self.project_name}', status='{self.status}')>"


class JobProgress(Base):
    """Tracks progress of each pipeline stage for a job."""
    __tablename__ = "job_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(50), nullable=False)
    percent = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    job = relationship("Job", back_populates="progress")

    def __repr__(self):
        return f"<JobProgress(job_id={self.job_id}, stage='{self.stage}', percent={self.percent})>"


class JobLog(Base):
    """Log entries for a job."""
    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(10), nullable=False)  # info | warn | error | debug
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    job = relationship("Job", back_populates="logs")

    def __repr__(self):
        return f"<JobLog(job_id={self.job_id}, level='{self.level}')>"
