"""
File filter — respects .gitignore and applies default ignore patterns.
Determines which files should be analyzed and which should be skipped.

File size strategy:
  <= 700 KB        : Analyze normally
  700 KB – 3 MB   : Split internally into 4,000-5,000 token subchunks
  > 3 MB (generated/data): Skip entirely
  > 3 MB (source code)   : Split internally, capped at LARGE_SOURCE_FILE_MAX_TOKENS
"""
import os
import re
import fnmatch
from typing import List, Tuple
from runner.config import RunnerConfig


# Default ignore patterns (applied in addition to .gitignore)
DEFAULT_IGNORES = [
    # Dependencies
    "node_modules/", "vendor/", "venv/", ".venv/", "__pycache__/",
    "packages/", "bower_components/", ".tox/", "env/",
    # Build artifacts
    "dist/", "build/", "out/", "target/", ".next/", ".nuxt/",
    "_build/", "site-packages/",
    # Minified & maps
    "*.min.js", "*.min.css", "*.map",
    # Lock files
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Pipfile.lock", "composer.lock", "Gemfile.lock", "Cargo.lock",
    # Compiled
    "*.pyc", "*.pyo", "*.class", "*.o", "*.obj", "*.exe", "*.dll",
    "*.so", "*.dylib", "*.a", "*.lib",
    # Images
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.ico", "*.svg",
    "*.webp", "*.tiff",
    # Media
    "*.mp4", "*.mp3", "*.wav", "*.avi", "*.mov", "*.flv",
    # Archives
    "*.zip", "*.tar", "*.gz", "*.rar", "*.7z", "*.bz2",
    # Documents (non-code)
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx",
    # Fonts
    "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf",
    # VCS
    ".git/", ".svn/", ".hg/", ".bzr/",
    # IDE
    ".idea/", ".vscode/", "*.swp", "*.swo", ".project", ".classpath",
    # OS
    ".DS_Store", "Thumbs.db", "desktop.ini",
    # Misc
    "*.log", "*.tmp", "*.bak", "*.cache",
]


def parse_gitignore(repo_path: str) -> List[str]:
    """Parse .gitignore file and return patterns."""
    gitignore_path = os.path.join(repo_path, ".gitignore")
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def should_skip_file(
    file_path: str,
    gitignore_patterns: List[str],
) -> Tuple[bool, str]:
    """
    Determine if a file should be skipped.

    Returns:
        (should_skip, reason) — e.g. (True, "binary_image") or (False, "")
    """
    # Normalize path separators
    normalized = file_path.replace("\\", "/")
    basename = os.path.basename(normalized)

    # Check default ignore patterns
    for pattern in DEFAULT_IGNORES:
        if pattern.endswith("/"):
            # Directory pattern — check if any path component matches
            dir_name = pattern.rstrip("/")
            parts = normalized.split("/")
            if dir_name in parts:
                return True, f"default_ignore ({pattern})"
        elif "*" in pattern:
            # Glob pattern
            if fnmatch.fnmatch(basename, pattern):
                return True, f"default_ignore ({pattern})"
        else:
            # Exact file match
            if basename == pattern:
                return True, f"default_ignore ({pattern})"

    # Check .gitignore patterns
    for pattern in gitignore_patterns:
        negate = pattern.startswith("!")
        if negate:
            continue  # Skip negation patterns for simplicity

        clean = pattern.strip("/")
        if fnmatch.fnmatch(normalized, clean) or fnmatch.fnmatch(basename, clean):
            return True, f"gitignore ({pattern})"
        # Check as directory pattern
        if clean in normalized.split("/"):
            return True, f"gitignore ({pattern})"

    # Check file size (skip files > 500KB)
    # This will be checked during traversal when we have the full path

    return False, ""


# Extensions that strongly signal generated, minified, or pure-data files.
# Files >3 MB with these extensions are skipped instead of being chunked.
_GENERATED_OR_DATA_EXTENSIONS = frozenset({
    # Data / serialised
    ".json", ".jsonl", ".ndjson",
    ".csv", ".tsv",
    ".parquet", ".arrow", ".feather",
    ".pkl", ".pickle",
    ".db", ".sqlite", ".sqlite3",
    ".pb", ".onnx",   # protobuf / ML models
    # Generated / minified web assets
    ".min.js", ".bundle.js",   # checked by endswith below
    ".map",
    # Generated documentation
    ".xml", ".xsd", ".wsdl",
    # Notebooks (large JSON blobs)
    ".ipynb",
    # Binary / compiled
    ".bin", ".dat",
})

# Source code extensions — files >3 MB with these will be split, not skipped.
_SOURCE_CODE_EXTENSIONS = frozenset({
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".kts",
    ".go", ".rs",
    ".rb", ".php",
    ".cs", ".cpp", ".c", ".h", ".hpp",
    ".swift", ".scala", ".clj", ".cljs",
    ".r", ".R",
    ".sql",
    ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".html", ".css", ".scss", ".less",
    ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".md", ".rst",
    ".tf",              # Terraform
    ".proto",           # Protobuf definitions (not compiled)
    ".graphql", ".gql",
    ".dockerfile",
})


def is_generated_or_data_file(file_path: str) -> bool:
    """
    Return True when the file is very likely generated, minified, or a data
    dump (and therefore not useful to send to an LLM for doc generation).

    Used to decide what to do with files that exceed MAX_FILE_SIZE_SKIP_BYTES.
    """
    name_lower = os.path.basename(file_path).lower()
    ext = os.path.splitext(name_lower)[1]  # e.g. ".json"

    # Multi-part extensions like ".min.js" or ".bundle.js"
    if name_lower.endswith(".min.js") or name_lower.endswith(".bundle.js"):
        return True

    if ext in _GENERATED_OR_DATA_EXTENSIONS:
        return True

    # If the extension is *not* a recognised source file, assume it is data
    if ext and ext not in _SOURCE_CODE_EXTENSIONS:
        return True

    return False


def evaluate_file_size(
    full_path: str,
    skip_bytes: int = None,
    chunk_bytes: int = None,
) -> Tuple[str, str, int]:
    """
    Evaluate a file against the three-tier size strategy:

      <= 700 KB            -> 'normal'
      700 KB – 3 MB        -> 'chunk_internally'
      > 3 MB, generated    -> 'skip'
      > 3 MB, source code  -> 'large_source'  (chunk with token cap)

    Returns:
        (action, reason, size_bytes)
        action is one of: 'skip' | 'chunk_internally' | 'normal' | 'large_source'
    """
    if skip_bytes is None:
        skip_bytes = RunnerConfig.MAX_FILE_SIZE_SKIP_BYTES
    if chunk_bytes is None:
        chunk_bytes = RunnerConfig.LARGE_FILE_CHUNK_BYTES

    try:
        size = os.path.getsize(full_path)
    except OSError:
        return "skip", "file_unreadable", 0

    if size <= chunk_bytes:
        return "normal", "", size

    if size <= skip_bytes:
        # 700 KB < size <= 3 MB
        return "chunk_internally", "", size

    # size > 3 MB — check whether it is worth splitting
    if is_generated_or_data_file(full_path):
        return "skip", f"large_generated_or_data ({size:,} bytes > 3 MB)", size

    # Source-code file over 3 MB — split internally with token cap
    return "large_source", "", size


def get_file_size_skip(full_path: str, max_bytes: int = None) -> Tuple[bool, str]:
    """Check if file will be skipped due to size/type. Provided for backward compatibility."""
    action, reason, _ = evaluate_file_size(full_path, skip_bytes=max_bytes)
    if action == "skip":
        return True, reason
    return False, ""


def discover_files(repo_path: str) -> List[dict]:
    """
    Discover all files in a repository, marking each as analyzed or skipped.

    File-info dict keys:
      path             : relative path from repo root
      status           : 'analyzed' | 'skipped'
      skip_reason      : human-readable reason when status=='skipped'
      size             : file size in bytes
      chunk_internally : True when the file should be split into subchunks
      large_source     : True when the file is >3 MB source code (token-capped split)

    Returns:
        List of file-info dicts.
    """
    gitignore_patterns = parse_gitignore(repo_path)
    files = []

    for root, dirs, filenames in os.walk(repo_path):
        # Skip .git directory entirely
        if ".git" in dirs:
            dirs.remove(".git")

        rel_root = os.path.relpath(root, repo_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        # Check if directory itself should be skipped
        skip_dir, _ = should_skip_file(rel_root + "/", gitignore_patterns)
        if skip_dir and rel_root:
            dirs.clear()  # Don't recurse into skipped directories
            continue

        for filename in filenames:
            rel_path = os.path.join(rel_root, filename).replace("\\", "/") if rel_root else filename
            full_path = os.path.join(root, filename)

            # Check if file should be skipped by gitignore / default ignores
            skip, reason = should_skip_file(rel_path, gitignore_patterns)
            if skip:
                files.append({
                    "path": rel_path,
                    "status": "skipped",
                    "skip_reason": reason,
                    "size": 0,
                    "chunk_internally": False,
                    "large_source": False,
                })
                continue

            # Apply three-tier size strategy
            action, size_reason, size = evaluate_file_size(full_path)

            if action == "skip":
                files.append({
                    "path": rel_path,
                    "status": "skipped",
                    "skip_reason": size_reason,
                    "size": size,
                    "chunk_internally": False,
                    "large_source": False,
                })
                continue

            files.append({
                "path": rel_path,
                "status": "analyzed",
                "skip_reason": "",
                "chunk_internally": action == "chunk_internally",
                "large_source": action == "large_source",
                "size": size,
            })

    return files

