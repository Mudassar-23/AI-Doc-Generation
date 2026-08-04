import os
import shutil
import stat
import subprocess
import re
from runner.config import RunnerConfig


def safe_rmtree(target_dir: str) -> None:
    """
    Safely remove a directory tree on Windows/Linux, handling read-only files
    and retrying if file locks are briefly held.
    """
    import time
    if not target_dir or not os.path.exists(target_dir):
        return

    target_dir = os.path.abspath(target_dir)

    def _make_writable(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    for attempt in range(3):
        try:
            shutil.rmtree(target_dir, onerror=_make_writable)
        except Exception:
            pass

        if not os.path.exists(target_dir):
            return

        # Walk and force unlink read-only files
        for root, dirs, files in os.walk(target_dir, topdown=False):
            for f in files:
                filepath = os.path.join(root, f)
                try:
                    os.chmod(filepath, stat.S_IWRITE)
                    os.unlink(filepath)
                except Exception:
                    pass
            for d in dirs:
                dirpath = os.path.join(root, d)
                try:
                    os.chmod(dirpath, stat.S_IWRITE)
                    os.rmdir(dirpath)
                except Exception:
                    pass
        try:
            os.rmdir(target_dir)
        except Exception:
            pass

        if not os.path.exists(target_dir):
            return
        time.sleep(0.2)



def cleanup_temp(job_id_or_path) -> None:
    """Clean up temporary repository directory."""
    if isinstance(job_id_or_path, int):
        temp_dir = os.path.abspath(os.path.join(RunnerConfig.TEMP_DIR, f"job_{job_id_or_path}"))
    else:
        temp_dir = os.path.abspath(str(job_id_or_path))

    safe_rmtree(temp_dir)


def clone_repository(repo_url: str, source_type: str, job_id: int) -> str:
    """
    Clone a repository to a temporary directory.
    Uses absolute path construction to fix double-nested cwd paths in subprocess calls.

    Args:
        repo_url: The repository URL.
        source_type: "github" or "azure_devops".
        job_id: Job ID for unique temp directory.

    Returns:
        Path to the cloned repository directory (absolute path).
    """
    # 1. ALWAYS convert to absolute paths. This prevents path nesting issues 
    # where relative paths like './tmp/job_x/repo' are evaluated relative to 
    # the subprocess cwd (which is also './tmp/job_x'), creating double nesting
    # like './tmp/job_x/tmp/job_x/repo'.
    temp_dir = os.path.abspath(os.path.join(RunnerConfig.TEMP_DIR, f"job_{job_id}"))
    repo_dir = os.path.abspath(os.path.join(temp_dir, "repo"))

    # Log target paths
    print(f"[Clone] Target absolute temp directory: {temp_dir}")
    print(f"[Clone] Target absolute repo directory: {repo_dir}")

    # 2. Re-create temp directory cleanly
    if os.path.exists(temp_dir):
        print(f"[Clone] Cleaning existing directory: {temp_dir}")
        safe_rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 3. Construct git clone command (shallow clone for performance)
        cmd = ["git", "clone", "--depth", "1", repo_url, repo_dir]
        print(f"[Clone] Running command: {' '.join(_sanitize_error(' '.join(cmd)).split())}")

        # 4. Run git clone process
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes
            cwd=temp_dir,
        )

        # Log process stdout/stderr
        print(f"[Clone] Git exit code: {result.returncode}")
        if result.stdout.strip():
            print(f"[Clone] Git stdout: {result.stdout.strip()}")
        if result.stderr.strip():
            # Sanitize stderr for logging so tokens/secrets are never printed
            print(f"[Clone] Git stderr: {_sanitize_error(result.stderr.strip())}")

        # 5. Check git exit code
        if result.returncode != 0:
            stderr_lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
            fatal_lines = [line for line in stderr_lines if not line.startswith("Cloning into")]
            raw_err = "\n".join(fatal_lines) if fatal_lines else (result.stderr.strip() or "Git clone failed")
            error_msg = _sanitize_error(raw_err)
            cleanup_temp(temp_dir)
            raise RuntimeError(f"Git clone failed: {error_msg}")

        # 6. Verify destination directory exists after cloning
        exists = os.path.exists(repo_dir)
        print(f"[Clone] Expected repo path: {repo_dir}")
        print(f"[Clone] Destination directory exists after clone: {exists}")

        if not exists:
            stderr_lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
            fatal_lines = [line for line in stderr_lines if not line.startswith("Cloning into")]
            raw_err = "\n".join(fatal_lines) if fatal_lines else "Directory not created"
            error_msg = _sanitize_error(raw_err)
            cleanup_temp(temp_dir)
            raise RuntimeError(f"Git clone failed: {error_msg} (directory not found at {repo_dir})")

        return repo_dir

    except subprocess.TimeoutExpired:
        cleanup_temp(temp_dir)
        raise RuntimeError("Git clone timed out (5 minutes). Repository may be too large.")
    except FileNotFoundError:
        raise RuntimeError("Git is not installed. Please install Git and try again.")


def _sanitize_error(msg: str) -> str:
    """Remove potential secrets from error messages."""
    msg = re.sub(r'ghp_[A-Za-z0-9_]{36,}', '***REDACTED***', msg)
    msg = re.sub(r'github_pat_[A-Za-z0-9_]{30,}', '***REDACTED***', msg)
    msg = re.sub(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer ***REDACTED***', msg)
    msg = re.sub(r'https?://[^@]+@', 'https://***REDACTED***@', msg)
    return msg
