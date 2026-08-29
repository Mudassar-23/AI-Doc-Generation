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


def _build_authenticated_url(repo_url: str, source_type: str) -> str:
    """
    Inject a Personal Access Token (PAT) into the repo URL so that
    `git clone` authenticates without relying on the system credential manager.

    Azure DevOps format : https://<PAT>@dev.azure.com/org/project/_git/repo
    GitHub format       : https://<PAT>@github.com/owner/repo.git

    Returns the original URL unchanged when no PAT is configured or the
    source type is unrecognised.
    """
    from urllib.parse import urlparse, urlunparse, quote

    parsed = urlparse(repo_url)

    # Only inject for HTTPS URLs without existing credentials
    if parsed.scheme not in ("https", "http") or parsed.username:
        return repo_url

    pat = ""
    if source_type == "azure_devops":
        pat = RunnerConfig.ADO_PAT
    elif source_type == "github":
        pat = RunnerConfig.GITHUB_PAT

    if not pat:
        print(f"[Clone] WARNING: No PAT configured for source_type='{source_type}'. "
              "Clone will rely on system credential manager.")
        return repo_url

    # URL-encode the PAT in case it contains special chars
    encoded_pat = quote(pat, safe="")

    # Rebuild URL with PAT as the username (empty password)
    authed = parsed._replace(netloc=f"{encoded_pat}@{parsed.hostname}"
                             + (f":{parsed.port}" if parsed.port else ""))
    return urlunparse(authed)


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

    # Log target paths (sanitized — never expose PATs)
    print(f"[Clone] Target absolute temp directory: {temp_dir}")
    print(f"[Clone] Target absolute repo directory: {repo_dir}")
    print(f"[Clone] Source type: {source_type}")

    # 2. Re-create temp directory cleanly
    if os.path.exists(temp_dir):
        print(f"[Clone] Cleaning existing directory: {temp_dir}")
        safe_rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 3. Build an authenticated URL by injecting the PAT
        authed_url = _build_authenticated_url(repo_url, source_type)
        print(f"[Clone] Authenticated URL: {_sanitize_error(authed_url)}")

        # 4. Construct git clone command (shallow clone for performance)
        #    -c core.longpaths=true  → enables long file paths on Windows (>260 chars)
        cmd = [
            "git",
            "-c", "core.longpaths=true",
            "clone", "--depth", "1",
            authed_url, repo_dir,
        ]
        print(f"[Clone] Running command: {_sanitize_error(' '.join(cmd))}")

        # 5. Prepare environment — inherit current env + add SSL cert if set
        clone_env = os.environ.copy()
        ssl_cert = RunnerConfig.SSL_CERT_FILE
        if ssl_cert and os.path.isfile(ssl_cert):
            clone_env["GIT_SSL_CAINFO"] = ssl_cert
            print(f"[Clone] Using SSL cert: {ssl_cert}")

        # 6. Run git clone process
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes — large repos need more time
            cwd=temp_dir,
            env=clone_env,
        )

        # Log process stdout/stderr (filter noisy progress lines for readability)
        print(f"[Clone] Git exit code: {result.returncode}")
        if result.stdout.strip():
            print(f"[Clone] Git stdout: {_sanitize_error(result.stdout.strip())}")
        if result.stderr.strip():
            # Only log meaningful lines, not thousands of 'Updating files:' progress
            meaningful_stderr = _filter_stderr(result.stderr.strip())
            if meaningful_stderr:
                print(f"[Clone] Git stderr: {_sanitize_error(meaningful_stderr)}")

        # 7. Check git exit code
        if result.returncode != 0:
            stderr_text = result.stderr or ""

            # Special case: "Clone succeeded, but checkout failed" is recoverable.
            # Git has all objects — only a few files with very long paths couldn't
            # be written to the working tree. We can proceed with what we have.
            if "Clone succeeded, but checkout failed" in stderr_text:
                print("[Clone] WARNING: Clone succeeded but checkout was partial. "
                      "Some files with very long paths could not be created. Proceeding anyway.")
                # Force-checkout what we can with long paths enabled
                subprocess.run(
                    ["git", "-c", "core.longpaths=true", "checkout", "-f"],
                    capture_output=True, text=True, timeout=120,
                    cwd=repo_dir, env=clone_env,
                )
            else:
                error_msg = _sanitize_error(_filter_stderr(stderr_text) or "Git clone failed")
                cleanup_temp(temp_dir)
                raise RuntimeError(f"Git clone failed: {error_msg}")

        # 8. Verify destination directory exists after cloning
        exists = os.path.exists(repo_dir)
        print(f"[Clone] Expected repo path: {repo_dir}")
        print(f"[Clone] Destination directory exists after clone: {exists}")

        if not exists:
            raw_err = _filter_stderr(result.stderr or "") or "Directory not created"
            error_msg = _sanitize_error(raw_err)
            cleanup_temp(temp_dir)
            raise RuntimeError(f"Git clone failed: {error_msg} (directory not found at {repo_dir})")

        return repo_dir

    except subprocess.TimeoutExpired:
        cleanup_temp(temp_dir)
        raise RuntimeError("Git clone timed out (10 minutes). Repository may be too large.")
    except FileNotFoundError:
        raise RuntimeError("Git is not installed. Please install Git and try again.")


def _filter_stderr(stderr: str) -> str:
    """
    Filter out noisy git progress lines from stderr, keeping only meaningful
    error / warning / fatal messages. This prevents error messages from being
    thousands of lines of 'Updating files:  xx%' progress output.
    """
    if not stderr:
        return ""
    noise_prefixes = (
        "Cloning into",
        "Updating files:",
        "Receiving objects:",
        "Resolving deltas:",
        "Counting objects:",
        "Compressing objects:",
        "remote: Counting",
        "remote: Compressing",
        "remote: Total",
    )
    lines = [
        line.strip() for line in stderr.splitlines()
        if line.strip() and not line.strip().startswith(noise_prefixes)
    ]
    return "\n".join(lines)


def _sanitize_error(msg: str) -> str:
    """Remove potential secrets from error messages."""
    # Redact the actual configured PAT values first (before URL-pattern matching
    # which would only catch the URL-embedded form)
    for pat_val in (RunnerConfig.ADO_PAT, RunnerConfig.GITHUB_PAT):
        if pat_val:
            msg = msg.replace(pat_val, "***REDACTED***")
    msg = re.sub(r'ghp_[A-Za-z0-9_]{36,}', '***REDACTED***', msg)
    msg = re.sub(r'github_pat_[A-Za-z0-9_]{30,}', '***REDACTED***', msg)
    msg = re.sub(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer ***REDACTED***', msg)
    msg = re.sub(r'https?://[^@]+@', 'https://***REDACTED***@', msg)
    return msg
