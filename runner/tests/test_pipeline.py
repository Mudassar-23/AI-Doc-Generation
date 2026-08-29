import os
import shutil
try:
    import pytest
except ImportError:
    class pytest:
        @staticmethod
        def fixture(func):
            return func

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Job, JobProgress, JobLog
from runner.config import RunnerConfig
from runner.stage_manager import StageManager
from runner.providers.fallback_provider import FallbackProvider
from runner.stages.s1_clone import clone_repository, cleanup_temp


@pytest.fixture
def db_session():
    """Fixture to build a clean in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_fallback_provider_sequence():
    """Verify FallbackProvider falls back from failed provider to Azure and then Mock."""
    fallback = FallbackProvider(preferred_provider_name="abacus")

    # Force Abacus and Azure to raise exceptions to simulate API/key failure
    def raise_err(*args, **kwargs):
        raise RuntimeError("API Key Invalid or Rate Limited")

    fallback.abacus.analyze_chunk = raise_err
    fallback.azure.analyze_chunk = raise_err

    # Test chunk analysis fallback to Mock
    result = fallback.analyze_chunk("System Prompt", "User Prompt")
    assert "[Mock Analysis]" in result

    # Test template filling fallback to Mock
    fallback.abacus.fill_template = raise_err
    fallback.azure.fill_template = raise_err

    filled = fallback.fill_template(
        "System Rules",
        "## Template:\nHello {Project Name}\n## Structured Context:\n{}"
    )
    assert "Hello Mock Project" in filled


def test_clone_repository_and_cleanup(tmp_path):
    """Test repository clone and cleanup with absolute path validation."""
    old_temp = RunnerConfig.TEMP_DIR
    RunnerConfig.TEMP_DIR = str(tmp_path)

    try:
        # Clone a public repository
        repo_url = "https://github.com/Mudassar-23/House-Price-Prediction-App"
        path = clone_repository(repo_url, "github", 777)

        # Assert absolute paths are resolved and verify filesystem directories
        assert os.path.isabs(path)
        assert os.path.exists(path)
        assert os.path.exists(os.path.join(path, ".git"))

        # Test cleanup unlinks all read-only files safely
        cleanup_temp(777)
        assert not os.path.exists(path)
    finally:
        RunnerConfig.TEMP_DIR = old_temp


def test_stage_manager_pipeline(db_session, tmp_path):
    """Verify that StageManager executes all 7 pipeline stages successfully in Mock mode."""
    old_temp = RunnerConfig.TEMP_DIR
    old_output = RunnerConfig.OUTPUT_DIR
    RunnerConfig.TEMP_DIR = str(tmp_path / "tmp")
    RunnerConfig.OUTPUT_DIR = str(tmp_path / "outputs")

    try:
        # Create test job in database
        job = Job(
            project_name="Test Project",
            repo_url="https://github.com/Mudassar-23/House-Price-Prediction-App",
            source_type="github",
            ai_provider="mock",
            status="queued"
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        # Instantiate StageManager with FallbackProvider preferring 'mock'
        provider = FallbackProvider(preferred_provider_name="mock")
        manager = StageManager(db=db_session, provider=provider)

        # Run job pipeline
        manager.run_job(job)

        # Refresh and verify results
        db_session.refresh(job)
        assert job.status == "completed"
        assert job.zip_generated is True
        assert job.zip_path is not None
        assert os.path.exists(job.zip_path)

        # Verify progress entries exist for all 7 stages
        progress_entries = db_session.query(JobProgress).filter(JobProgress.job_id == job.id).all()
        stages = [p.stage for p in progress_entries]
        expected_stages = [
            "cloning", "analyzing", "chunking", "llm_analysis",
            "context_building", "template_filling", "packaging"
        ]
        for stage in expected_stages:
            assert stage in stages

        # Verify log entries exist in database
        logs = db_session.query(JobLog).filter(JobLog.job_id == job.id).all()
        assert len(logs) > 0
        assert any("Pipeline completed successfully" in l.message for l in logs)
    finally:
        RunnerConfig.TEMP_DIR = old_temp
        RunnerConfig.OUTPUT_DIR = old_output


def test_chunking_and_file_filters(tmp_path):
    """Verify target ~4000 tokens, max ~5000 tokens, 3MB skip, 700KB internal chunking, and non-truncating >8000 token logic."""
    from runner.analysis.file_filter import evaluate_file_size
    from runner.analysis.chunk_builder import read_file_content, build_chunks

    test_dir = str(tmp_path / "filter_test")
    os.makedirs(test_dir, exist_ok=True)

    # 1. Test evaluate_file_size thresholds
    small_file = os.path.join(test_dir, "small.txt")
    with open(small_file, "w") as f:
        f.write("a" * 100)
    action, _, _ = evaluate_file_size(small_file)
    assert action == "normal"

    large_file = os.path.join(test_dir, "large.txt")
    with open(large_file, "w") as f:
        f.write(("a" * 100 + "\n") * 7500)  # ~750 KB > 700 KB with lines

    action, _, _ = evaluate_file_size(large_file)
    assert action == "chunk_internally"

    huge_file = os.path.join(test_dir, "huge.txt")
    with open(huge_file, "w") as f:
        f.write("a" * (3 * 1024 * 1024 + 100))  # > 3 MB
    action, _, _ = evaluate_file_size(huge_file)
    assert action == "skip"

    # 2. Test reading > 8000 token file without truncation
    big_code_file = os.path.join(test_dir, "big_code.py")
    big_content = "# line\n" * 5000  # ~35,000 chars => ~8,750 tokens (> 8000 tokens)
    with open(big_code_file, "w") as f:
        f.write(big_content)

    content = read_file_content(big_code_file)
    assert "[... TRUNCATED" not in content
    assert len(content) == len(big_content)

    # 3. Test build_chunks with internal chunking for large file
    analyzed_files = [
        {"path": "large.txt", "category": "General", "size": 750 * 1024, "chunk_internally": True}
    ]
    chunks = build_chunks(test_dir, analyzed_files)
    assert len(chunks) > 1  # Large file split into multiple parts
    for chunk in chunks:
        assert chunk["estimated_tokens"] <= RunnerConfig.MAX_CHUNK_TOKENS + 100

