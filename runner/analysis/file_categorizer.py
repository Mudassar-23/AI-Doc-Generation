"""
File categorizer — assigns files to semantic categories.
"""
import os
import re
from typing import Optional


# Category definitions with pattern matching rules
# Priority order: lower index = higher priority
CATEGORY_RULES = [
    {
        "name": "Documentation",
        "priority": 1,
        "patterns": [
            "README*", "CHANGELOG*", "CONTRIBUTING*", "LICENSE*",
            "docs/**", "doc/**", "*.md",
        ],
        "path_contains": ["docs/", "doc/", "documentation/"],
    },
    {
        "name": "Configuration",
        "priority": 2,
        "patterns": [
            "*.config.*", "*.env*", "*.toml", "*.yaml", "*.yml",
            "*.ini", "*.cfg", "settings.*", "config.*",
            ".babelrc", ".eslintrc*", "tsconfig*", "jest.config*",
            "setup.py", "setup.cfg", "pyproject.toml",
        ],
        "path_contains": ["config/", "configuration/", "settings/"],
    },
    {
        "name": "Models / Database",
        "priority": 3,
        "patterns": [
            "*.sql", "schema.*",
        ],
        "path_contains": [
            "models/", "model/", "schema/", "schemas/", "migrations/",
            "entities/", "entity/", "database/", "db/",
        ],
    },
    {
        "name": "Services / Business Logic",
        "priority": 4,
        "patterns": [],
        "path_contains": [
            "services/", "service/", "business/", "logic/",
            "handlers/", "handler/", "domain/", "core/",
            "usecases/", "use_cases/",
        ],
    },
    {
        "name": "Controllers / Routes",
        "priority": 5,
        "patterns": [],
        "path_contains": [
            "controllers/", "controller/", "routes/", "route/",
            "api/", "endpoints/", "views/", "view/",
            "routers/", "router/",
        ],
    },
    {
        "name": "CI/CD & Docker",
        "priority": 6,
        "patterns": [
            "Dockerfile*", "docker-compose*", ".dockerignore",
            "Makefile", "Procfile", "Vagrantfile",
            "azure-pipelines*", "Jenkinsfile", ".travis.yml",
            "cloudbuild*", "appveyor*",
        ],
        "path_contains": [
            ".github/", ".gitlab/", ".circleci/",
            "deploy/", "deployment/", "infra/", "infrastructure/",
            "terraform/", "helm/", "k8s/", "kubernetes/",
        ],
    },
    {
        "name": "Tests",
        "priority": 7,
        "patterns": [
            "*_test.*", "*.test.*", "*.spec.*", "*_spec.*",
            "test_*", "conftest.py",
        ],
        "path_contains": [
            "test/", "tests/", "spec/", "specs/",
            "__tests__/", "testing/",
        ],
    },
    {
        "name": "Utilities / Helpers",
        "priority": 8,
        "patterns": [],
        "path_contains": [
            "utils/", "util/", "utilities/", "helpers/",
            "lib/", "common/", "shared/", "tools/",
        ],
    },
]


def categorize_file(file_path: str) -> str:
    """
    Assign a category to a file based on its path and name.

    Returns:
        Category name string (e.g., "Controllers / Routes", "Models / Database")
    """
    normalized = file_path.replace("\\", "/").lower()
    basename = os.path.basename(file_path).lower()

    for rule in CATEGORY_RULES:
        # Check path_contains patterns
        for pattern in rule.get("path_contains", []):
            if pattern in normalized:
                return rule["name"]

        # Check filename patterns (using simple matching)
        for pattern in rule.get("patterns", []):
            pattern_lower = pattern.lower()
            if "**" in pattern_lower:
                # Directory glob — check if basename matches the part after **
                suffix = pattern_lower.split("**/")[-1]
                if _matches_glob(basename, suffix):
                    return rule["name"]
            elif "*" in pattern_lower:
                if _matches_glob(basename, pattern_lower):
                    return rule["name"]
            else:
                if basename == pattern_lower:
                    return rule["name"]

    return "General"


def _matches_glob(name: str, pattern: str) -> bool:
    """Simple glob matching for filenames."""
    # Convert glob to regex
    regex = pattern.replace(".", "\\.").replace("*", ".*")
    try:
        return bool(re.match(f"^{regex}$", name, re.IGNORECASE))
    except re.error:
        return False


def detect_language(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    language_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript (React)",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".java": "Java",
        ".kt": "Kotlin",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".swift": "Swift",
        ".scala": "Scala",
        ".r": "R",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".less": "LESS",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
        ".xml": "XML",
        ".toml": "TOML",
        ".ini": "INI",
        ".md": "Markdown",
        ".sh": "Shell",
        ".bash": "Bash",
        ".ps1": "PowerShell",
        ".bat": "Batch",
        ".dockerfile": "Dockerfile",
    }
    # Special case for Dockerfile (no extension)
    basename = os.path.basename(file_path).lower()
    if basename.startswith("dockerfile"):
        return "Dockerfile"
    if basename == "makefile":
        return "Makefile"

    return language_map.get(ext)
