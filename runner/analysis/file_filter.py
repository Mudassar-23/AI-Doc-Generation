"""
File filter — respects .gitignore and applies default ignore patterns.
Determines which files should be analyzed and which should be skipped.

File size strategy:
  <= 700 KB        : Analyze normally
  700 KB – 3 MB   : Split internally into 4,000-5,000 token subchunks
  > 3 MB (generated/data): Skip entirely
  > 3 MB (source code)   : Split internally, capped at LARGE_SOURCE_FILE_MAX_TOKENS

File triage strategy (for large .NET / enterprise repos):
  - Skip vendor/dependency directories (packages, UI.Assemblies, etc.)
  - Skip auto-generated files (*.Designer.cs, Reference.cs, Web References/)
  - Skip VS metadata (*.resx, *.datasource, *.xsd, *.disco, *.wsdl, etc.)
  - Skip test directories (Test*, IntegrationTests) — configurable
  - Skip client/UI directories (Client/) — configurable
  - Skip vendor JS libraries (jQuery, Bootstrap, etc.) — configurable
  - Content-header scan for auto-generated markers — configurable
"""
import os
import re
import fnmatch
from typing import List, Tuple
from runner.config import RunnerConfig


# ──────────────────────────────────────────────────────────────────────
# 1. DEFAULT IGNORE PATTERNS (applied in addition to .gitignore)
# ──────────────────────────────────────────────────────────────────────
DEFAULT_IGNORES = [
    # ── Dependencies ──
    "node_modules/", "vendor/", "venv/", ".venv/", "__pycache__/",
    "packages/", "bower_components/", ".tox/", "env/",

    # ── Build artifacts ──
    "dist/", "build/", "out/", "target/", ".next/", ".nuxt/",
    "_build/", "site-packages/",
    # .NET build output
    "bin/", "obj/", "debug/", "release/",

    # ── Minified & maps ──
    "*.min.js", "*.min.css", "*.map",

    # ── Lock files ──
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Pipfile.lock", "composer.lock", "Gemfile.lock", "Cargo.lock",

    # ── Compiled / binary ──
    "*.pyc", "*.pyo", "*.class", "*.o", "*.obj", "*.exe", "*.dll",
    "*.so", "*.dylib", "*.a", "*.lib",
    "*.pdb",           # Debug symbols
    "*.nupkg",         # NuGet packages
    "*.p7s",           # Digital signatures
    "*.snk",           # Strong-name key files
    "*.pfx",           # Certificate files
    "*.ocx",           # ActiveX controls
    "*.cab",           # Windows cabinet archives

    # ── Images ──
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.ico", "*.svg",
    "*.webp", "*.tiff", "*.tif",

    # ── Media ──
    "*.mp4", "*.mp3", "*.wav", "*.avi", "*.mov", "*.flv",

    # ── Archives ──
    "*.zip", "*.tar", "*.gz", "*.rar", "*.7z", "*.bz2",

    # ── Documents (non-code) ──
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx",
    "*.rtf",           # Rich text
    "*.mdb",           # MS Access database

    # ── Fonts ──
    "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf",

    # ── VCS ──
    ".git/", ".svn/", ".hg/", ".bzr/",

    # ── IDE ──
    ".idea/", ".vscode/", "*.swp", "*.swo", ".project", ".classpath",

    # ── OS ──
    ".DS_Store", "Thumbs.db", "desktop.ini",

    # ── Misc ──
    "*.log", "*.tmp", "*.bak", "*.cache",

    # ── Visual Studio generated / metadata ──
    "*.Designer.cs", "*.Designer.vb",     # WinForms / WPF designer code-behind
    "*.designer.cs", "*.designer.vb",     # Case-insensitive fallback
    "*.resx",                              # Resource XML (localisation strings)
    "*.datasource",                        # VS DataSource metadata
    "*.xsx", "*.xsc", "*.xss",            # DataSet generated files
    "*.xsd",                               # XML schema definitions (DataSet schemas)
    "*.cd",                                # Class diagrams
    "*.settings",                          # VS settings files
    "*.licx",                              # License files

    # ── WCF / SOAP service metadata ──
    "*.disco", "*.wsdl", "*.svcinfo", "*.svcmap",

    # ── Crystal Reports (binary format, unreadable by LLM) ──
    "*.rpt",

    # ── .NET project & solution files (declarative, no business logic) ──
    "*.csproj", "*.vbproj", "*.vdproj", "*.sln",
    "*.vssscc", "*.vspscc", "*.scc",      # Source control bindings
    "*.vs10x",
    "*.testsettings",
    "*.pubxml",

    # ── MSBuild files ──
    "*.targets", "*.props", "*.rsp",

    # ── XAML UI markup ──
    "*.xaml",

    # ── .NET config files ──
    "*.config",

    # ── WCF / web endpoint declarations (very short, no logic) ──
    "*.asmx", "*.svc", "*.asax",
]


# ──────────────────────────────────────────────────────────────────────
# 2. DIRECTORY-LEVEL EXCLUSIONS
# ──────────────────────────────────────────────────────────────────────

# Directories to always skip — contain no useful business logic.
# Matched against any path component (case-sensitive).
SKIP_DIRECTORIES = frozenset({
    # Vendor / dependency assemblies
    "packages",
    "UI.Assemblies",
    "UI.Startup.Bin",
    "UI.Images",

    # Auto-generated SOAP / WCF proxy folders
    "Web References",
    "Service References",
})

# Test directory prefixes — matched against the top-level directory name.
# Only active when RunnerConfig.SKIP_TEST_DIRECTORIES is True.
TEST_DIRECTORY_PREFIXES = ("Test", "IntegrationTests")

# Client / UI directories — matched against the top-level directory name.
# Only active when RunnerConfig.SKIP_CLIENT_UI is True.
CLIENT_UI_DIRECTORIES = frozenset({
    "Client",
})


# ──────────────────────────────────────────────────────────────────────
# 3. AUTO-GENERATED CONTENT DETECTION (header scanning)
# ──────────────────────────────────────────────────────────────────────

# Markers found in the first ~2 KB of auto-generated files
AUTO_GENERATED_MARKERS = [
    "auto-generated",
    "autogenerated",
    "<auto-generated>",
    "do not edit",
    "do not modify",
    "generated by",
    "this code was generated",
    "designer generated code",
]

# Only scan these extensions for auto-gen headers (performance)
_AUTOGEN_SCAN_EXTENSIONS = frozenset({".cs", ".vb"})

# Special filename pattern: WCF / Web Service generated proxy classes
_GENERATED_FILENAMES = frozenset({"reference.cs", "reference.vb"})

# Bytes to read for header scanning
_HEADER_SCAN_BYTES = 2048


# ──────────────────────────────────────────────────────────────────────
# 4. VENDOR JS DETECTION
# ──────────────────────────────────────────────────────────────────────

# Common vendor JS library filename patterns (case-insensitive glob)
VENDOR_JS_PATTERNS = [
    "jquery*", "bootstrap*", "popper*", "modernizr*",
    "angular*", "react*", "vue*", "lodash*", "underscore*",
    "moment*", "d3*", "chart*",
]


# ──────────────────────────────────────────────────────────────────────
# 5. SIZE-BASED CLASSIFICATION (unchanged from original)
# ──────────────────────────────────────────────────────────────────────

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
    ".xml", ".xsd", ".wsdl",".html",".css",
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
    ".vb",              # Visual Basic .NET
})


# ═══════════════════════════════════════════════════════════════════════
# FILTER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

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


def _is_skip_directory(dir_name: str) -> Tuple[bool, str]:
    """
    Check if a directory name matches a hard-skip or configurable-skip list.

    Returns:
        (should_skip, reason)
    """
    # Always-skip directories
    if dir_name in SKIP_DIRECTORIES:
        return True, f"skip_directory ({dir_name})"

    # Test directories (configurable)
    if RunnerConfig.SKIP_TEST_DIRECTORIES:
        for prefix in TEST_DIRECTORY_PREFIXES:
            if dir_name == prefix or dir_name.startswith(prefix):
                return True, f"test_directory ({dir_name})"

    # Client / UI directories (configurable)
    if RunnerConfig.SKIP_CLIENT_UI:
        if dir_name in CLIENT_UI_DIRECTORIES:
            return True, f"client_ui ({dir_name})"

    return False, ""


def _is_vendor_js(file_path: str, basename: str) -> bool:
    """Check if a JS file is a common vendor library."""
    if not RunnerConfig.SKIP_VENDOR_JS:
        return False
    if not basename.lower().endswith(".js"):
        return False
    name_lower = basename.lower()
    for pattern in VENDOR_JS_PATTERNS:
        if fnmatch.fnmatch(name_lower, pattern):
            return True
    return False


def _has_autogen_header(full_path: str) -> bool:
    """
    Read the first ~2 KB of a file and check for auto-generation markers.
    Only called for .cs / .vb files when SKIP_AUTOGENERATED_CONTENT is enabled.
    """
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(_HEADER_SCAN_BYTES).lower()
        return any(marker in head for marker in AUTO_GENERATED_MARKERS)
    except (OSError, UnicodeDecodeError):
        return False


def should_skip_file(
    file_path: str,
    gitignore_patterns: List[str],
) -> Tuple[bool, str]:
    """
    Determine if a file should be skipped based on name and path patterns.

    Returns:
        (should_skip, reason) — e.g. (True, "binary_image") or (False, "")
    """
    # Normalize path separators
    normalized = file_path.replace("\\", "/")
    basename = os.path.basename(normalized)
    basename_lower = basename.lower()

    # ── Check default ignore patterns ──
    for pattern in DEFAULT_IGNORES:
        if pattern.endswith("/"):
            # Directory pattern — check if any path component matches
            dir_name = pattern.rstrip("/")
            parts = normalized.split("/")
            if dir_name in parts:
                return True, f"default_ignore ({pattern})"
            # Case-insensitive check for directory names
            parts_lower = [p.lower() for p in parts]
            if dir_name.lower() in parts_lower:
                return True, f"default_ignore ({pattern})"
        elif "*" in pattern:
            # Glob pattern — case-insensitive matching
            if fnmatch.fnmatch(basename_lower, pattern.lower()):
                return True, f"default_ignore ({pattern})"
        else:
            # Exact file match — case-insensitive
            if basename_lower == pattern.lower():
                return True, f"default_ignore ({pattern})"

    # ── Check for generated filename patterns ──
    if basename_lower in _GENERATED_FILENAMES:
        return True, f"auto_generated ({basename})"

    # ── Check for vendor JS ──
    if _is_vendor_js(normalized, basename):
        return True, f"vendor_js ({basename})"

    # ── Check .gitignore patterns ──
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

    return False, ""


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

    Applies a multi-layer triage:
      1. Directory-level pruning (vendor, test, client/UI, Web/Service References)
      2. Filename/extension pattern matching (DEFAULT_IGNORES + .gitignore)
      3. Content-header auto-generation scanning (for .cs / .vb files)
      4. Three-tier file size strategy

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

    def _record_dir_as_skipped(dir_full_path: str, reason: str):
        """Walk a pruned directory and record every file inside it as skipped."""
        for sub_root, sub_dirs, sub_files in os.walk(dir_full_path):
            if ".git" in sub_dirs:
                sub_dirs.remove(".git")
            for fn in sub_files:
                rel = os.path.relpath(
                    os.path.join(sub_root, fn), repo_path
                ).replace("\\", "/")
                files.append({
                    "path": rel,
                    "status": "skipped",
                    "skip_reason": reason,
                    "size": 0,
                    "chunk_internally": False,
                    "large_source": False,
                })

    for root, dirs, filenames in os.walk(repo_path):
        # Skip .git directory entirely
        if ".git" in dirs:
            dirs.remove(".git")

        rel_root = os.path.relpath(root, repo_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        # ── Layer 1: Directory-level pruning ──

        # Check if directory itself should be skipped by default ignores
        if rel_root:
            skip_dir, skip_reason = should_skip_file(rel_root + "/", gitignore_patterns)
            if skip_dir:
                # Record all files in this directory tree as skipped
                for fn in filenames:
                    rel_path = os.path.join(rel_root, fn).replace("\\", "/")
                    files.append({
                        "path": rel_path,
                        "status": "skipped",
                        "skip_reason": skip_reason,
                        "size": 0,
                        "chunk_internally": False,
                        "large_source": False,
                    })
                # Record all subdirectory files as skipped too
                for d in dirs:
                    _record_dir_as_skipped(os.path.join(root, d), skip_reason)
                dirs.clear()
                continue

        # Check directory-level exclusion lists (SKIP_DIRECTORIES, test, client)
        if rel_root:
            parts = rel_root.split("/")
            prune = False

            # Check every path component against SKIP_DIRECTORIES
            for part in parts:
                skip, reason = _is_skip_directory(part)
                if skip:
                    # Record current-level files
                    for fn in filenames:
                        rel_path = os.path.join(rel_root, fn).replace("\\", "/")
                        files.append({
                            "path": rel_path,
                            "status": "skipped",
                            "skip_reason": reason,
                            "size": 0,
                            "chunk_internally": False,
                            "large_source": False,
                        })
                    # Record all subdirectory files
                    for d in dirs:
                        _record_dir_as_skipped(os.path.join(root, d), reason)
                    dirs.clear()
                    prune = True
                    break
            if prune:
                continue

        # Prune subdirectories that match skip lists before recursing
        # (so os.walk won't enter them — we record their files now)
        dirs_to_remove = []
        for d in dirs:
            skip, reason = _is_skip_directory(d)
            if skip:
                _record_dir_as_skipped(os.path.join(root, d), reason)
                dirs_to_remove.append(d)
            else:
                # Also check if the subdir would be caught by should_skip_file
                sub_rel = os.path.join(rel_root, d).replace("\\", "/") if rel_root else d
                skip_sub, sub_reason = should_skip_file(sub_rel + "/", gitignore_patterns)
                if skip_sub:
                    _record_dir_as_skipped(os.path.join(root, d), sub_reason)
                    dirs_to_remove.append(d)
        for d in dirs_to_remove:
            dirs.remove(d)

        # ── Layer 2 & 3: File-level filtering ──
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

            # Content-header auto-generation scan (.cs / .vb only)
            if RunnerConfig.SKIP_AUTOGENERATED_CONTENT:
                ext = os.path.splitext(filename)[1].lower()
                if ext in _AUTOGEN_SCAN_EXTENSIONS:
                    if _has_autogen_header(full_path):
                        files.append({
                            "path": rel_path,
                            "status": "skipped",
                            "skip_reason": f"auto_generated_content ({filename})",
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



