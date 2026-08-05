"""
Stage Manager — orchestrates the documentation generation pipeline.

Pipeline:
  1. Clone Repository
  2. Analyze Repository
  3. Build Chunks
  3.5 Compute Embeddings (optional — Azure OpenAI, graceful skip if unavailable)
  4. LLM Chunk Analysis
  5. Build Structured Context
  6. Fill Templates (RAG-enhanced when embeddings are available)
  7. Package ZIP
"""
import sys
import os
import json
import traceback
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.models import Job, JobProgress, JobLog

from runner.stages.s1_clone import clone_repository, cleanup_temp
from runner.stages.s2_analyze import analyze_repository
from runner.stages.s3_chunk import build_file_chunks
from runner.stages.s4_llm_analyze import analyze_chunks_with_llm
from runner.stages.s5_context_build import build_structured_context
from runner.stages.s6_template_fill import fill_templates
from runner.stages.s7_package import package_documents
from runner.providers.base import BaseProvider
from runner.analysis.embeddings import AzureEmbedder
from runner.analysis.vector_store import ChunkVectorStore


STAGES = [
    "cloning",
    "analyzing",
    "chunking",
    "embedding",        # Stage 3.5 — skipped gracefully when unavailable
    "llm_analysis",
    "context_building",
    "template_filling",
    "packaging",
]


class StageManager:
    """Orchestrates the 7-stage pipeline for a single job."""

    def __init__(self, db: Session, provider: BaseProvider):
        self.db = db
        self.provider = provider
        self.embedder = AzureEmbedder()

    def run_job(self, job: Job):
        """Run the full pipeline for a job."""
        repo_path = None

        try:
            self._log(job.id, "info", f"Starting pipeline for '{job.project_name}'")
            self._update_job_status(job, "running")

            # Stage 1: Clone
            self._update_progress(job.id, "cloning", 0, "Cloning repository...")
            repo_path = clone_repository(job.repo_url, job.source_type, job.id)
            self._update_progress(job.id, "cloning", 100, "Repository cloned")
            self._log(job.id, "info", f"Cloned to {repo_path}")

            # Stage 2: Analyze
            self._update_progress(job.id, "analyzing", 0, "Analyzing repository structure...")
            analysis = analyze_repository(repo_path)
            self._update_progress(job.id, "analyzing", 100,
                f"Analyzed: {analysis['summary']['analyzed']} files, skipped: {analysis['summary']['skipped']}")
            self._log(job.id, "info",
                f"Analysis complete — {analysis['summary']['total']} total, "
                f"{analysis['summary']['analyzed']} analyzed, "
                f"{analysis['summary']['skipped']} skipped")

            # Stage 3: Build Chunks
            self._update_progress(job.id, "chunking", 0, "Building semantic chunks...")
            chunks = build_file_chunks(repo_path, analysis["analyzed_files"])
            chunk_total_tokens = sum(c.get("estimated_tokens", 0) for c in chunks)
            chunks_msg = f"{len(chunks)} chunks created"
            token_meta = json.dumps({"chunks_total": chunk_total_tokens, "num_chunks": len(chunks)})
            self._update_progress(job.id, "chunking", 100, f"TOKENS:{token_meta} {chunks_msg}")
            self._log(job.id, "info", f"Built {len(chunks)} chunks — {chunk_total_tokens:,} total tokens")

            # Stage 3.5: Compute Embeddings (optional)
            vector_store = self._run_embedding_stage(job, chunks)

            # Stage 4: LLM Chunk Analysis
            self._update_progress(job.id, "llm_analysis", 0, "Analyzing chunks with AI...")

            def llm_progress(chunk_num, total, message):
                pct = int((chunk_num / total) * 100)
                self._update_progress(job.id, "llm_analysis", pct, message)

            chunk_analyses = analyze_chunks_with_llm(
                provider=self.provider,
                chunks=chunks,
                project_name=job.project_name,
                repo_url=job.repo_url,
                progress_callback=llm_progress,
            )
            self._update_progress(job.id, "llm_analysis", 100,
                f"All {len(chunk_analyses)} chunks analyzed")
            self._log(job.id, "info", f"LLM analyzed {len(chunk_analyses)} chunks")

            # Stage 5: Build Structured Context
            self._update_progress(job.id, "context_building", 0, "Building structured context...")
            structured_context = build_structured_context(chunk_analyses)
            self._update_progress(job.id, "context_building", 100, "Context ready")
            self._log(job.id, "info", "Structured context built")

            # Stage 6: Fill Templates
            self._update_progress(job.id, "template_filling", 0, "Generating documents...")

            def template_progress(template_num, total, message):
                pct = int((template_num / total) * 100)
                self._update_progress(job.id, "template_filling", pct, message)

            documents, tmpl_in_tokens, tmpl_out_tokens = fill_templates(
                provider=self.provider,
                structured_context=structured_context,
                project_name=job.project_name,
                repo_url=job.repo_url,
                progress_callback=template_progress,
                vector_store=vector_store,
                embedder=self.embedder,
            )
            tmpl_meta = json.dumps({"tmpl_in": tmpl_in_tokens, "tmpl_out": tmpl_out_tokens, "num_docs": len(documents)})
            self._update_progress(job.id, "template_filling", 100,
                f"TOKENS:{tmpl_meta} All {len(documents)} documents generated")
            self._log(job.id, "info", f"Generated {len(documents)} documents — in: {tmpl_in_tokens:,} / out: {tmpl_out_tokens:,} tokens")

            # Stage 7: Package
            self._update_progress(job.id, "packaging", 0, "Creating ZIP package...")
            zip_path = package_documents(
                documents=documents,
                project_name=job.project_name,
                repo_url=job.repo_url,
                source_type=job.source_type,
                job_id=job.id,
            )
            self._update_progress(job.id, "packaging", 100, "ZIP ready")
            self._log(job.id, "info", f"ZIP created: {zip_path}")

            # Mark job as completed
            job.status = "completed"
            job.zip_generated = True
            job.zip_path = zip_path
            job.completed_at = datetime.utcnow()
            self.db.commit()

            self._log(job.id, "info", "Pipeline completed successfully")

        except Exception as e:
            # Mark job as failed
            error_msg = str(e)
            self._log(job.id, "error", f"Pipeline failed: {error_msg}")
            self._log(job.id, "error", traceback.format_exc())

            job.status = "failed"
            job.error_message = error_msg[:2000]  # Truncate long errors
            self.db.commit()

        finally:
            # Clean up temp directory
            if repo_path:
                cleanup_temp(job.id)

    # ------------------------------------------------------------------
    # Stage 3.5 — Embedding helper
    # ------------------------------------------------------------------

    def _run_embedding_stage(self, job, chunks: list):
        """
        Compute embeddings for all chunks and build a ChunkVectorStore.

        Returns a populated ChunkVectorStore on success, or None if embeddings
        are not configured / fail — in which case Stage 6 uses full context only.
        """
        if not self.embedder.is_available():
            self._log(job.id, "info",
                      "[Stage 3.5] Embeddings not configured — skipping (RAG will be inactive).")
            return None

        try:
            self._update_progress(
                job.id, "embedding", 0,
                f"Computing embeddings for {len(chunks)} chunks..."
            )
            self._log(job.id, "info",
                      f"[Stage 3.5] Starting embedding for {len(chunks)} chunks "
                      f"using '{self.embedder.deployment}'")

            # Embed all chunks (mutates chunk dicts in place, adds 'embedding' key)
            self.embedder.embed_chunks(chunks)

            # Build the vector index
            store = ChunkVectorStore()
            store.build(chunks)

            embedded_count = sum(1 for c in chunks if "embedding" in c)
            self._update_progress(
                job.id, "embedding", 100,
                f"Embedded {embedded_count}/{len(chunks)} chunks — vector index ready"
            )
            self._log(job.id, "info",
                      f"[Stage 3.5] Vector index built — {embedded_count} chunks indexed.")

            return store if store.is_built() else None

        except Exception as e:
            # Non-fatal — log and continue without RAG
            self._log(job.id, "info",
                      f"[Stage 3.5] Embedding failed ({e}) — pipeline continues without RAG.")
            self._update_progress(
                job.id, "embedding", 100,
                f"Skipped (error: {str(e)[:80]})"
            )
            return None

    def _update_progress(self, job_id: int, stage: str, percent: int, message: str):
        """Update or create progress entry for a stage."""
        progress = (
            self.db.query(JobProgress)
            .filter(JobProgress.job_id == job_id, JobProgress.stage == stage)
            .first()
        )
        if progress:
            progress.percent = percent
            progress.message = message
            progress.updated_at = datetime.utcnow()
        else:
            progress = JobProgress(
                job_id=job_id,
                stage=stage,
                percent=percent,
                message=message,
                updated_at=datetime.utcnow(),
            )
            self.db.add(progress)
        self.db.commit()

    def _update_job_status(self, job: Job, status: str):
        """Update job status."""
        job.status = status
        self.db.commit()

    def _log(self, job_id: int, level: str, message: str):
        """Add a log entry."""
        log = JobLog(
            job_id=job_id,
            level=level,
            message=message,
            created_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()
        print(f"[Job {job_id}] [{level.upper()}] {message}")
