"""
Mock AI Provider — returns deterministic, realistic responses for testing and development.

Features:
- Configurable delay to simulate LLM latency
- Detects languages and patterns from chunk content
- Returns structured JSON for chunk analysis
- Returns filled Markdown for template filling
- No API keys required
"""
import json
import time
import re
from runner.providers.base import BaseProvider
from runner.config import RunnerConfig


class MockProvider(BaseProvider):
    """Mock provider for testing — returns realistic pre-built responses."""

    def __init__(self):
        self.delay = RunnerConfig.MOCK_DELAY

    def analyze_chunk(self, system_prompt: str, user_prompt: str) -> str:
        """Return a realistic chunk analysis based on content heuristics."""
        time.sleep(self.delay)

        # Detect languages from the chunk content
        languages = self._detect_languages(user_prompt)
        endpoints = self._detect_endpoints(user_prompt)
        env_vars = self._detect_env_vars(user_prompt)
        tables = self._detect_tables(user_prompt)

        result = {
            "project_summary": "[Mock Analysis] Repository chunk analyzed. Contains source code and configuration files.",
            "tech_stack": languages,
            "architecture_notes": "[Mock] Standard application architecture detected with separation of concerns.",
            "database_tables": tables,
            "api_endpoints": endpoints,
            "authentication": {
                "type": "Unknown",
                "details": "[Mock] Authentication mechanism could not be determined from this chunk.",
                "source": "mock_analysis"
            },
            "configuration": {
                "env_vars": env_vars,
                "config_files": [],
                "source": ["mock_analysis"]
            },
            "business_logic": "[Mock] Business logic analysis — standard CRUD operations detected.",
            "dependencies": {
                "runtime": [],
                "dev": [],
                "source": "mock_analysis"
            },
            "folder_structure_notes": "[Mock] Standard project structure observed.",
            "security_notes": "[Mock] No specific security concerns identified in this chunk.",
            "deployment_notes": "[Mock] Deployment configuration not found in this chunk.",
            "ci_cd_notes": "[Mock] CI/CD configuration not found in this chunk.",
            "docker_notes": "[Mock] Docker configuration not found in this chunk.",
            "coding_patterns": "[Mock] Standard coding patterns observed.",
            "missing_features": "[Mock] Unable to determine missing features from this chunk alone.",
            "assumptions": "[Mock] This is a mock analysis — all findings are simulated.",
            "unknown_areas": "[Mock] Full analysis requires a real AI provider.",
            "source_files": ["mock_analysis"]
        }

        return json.dumps(result, indent=2)

    def fill_template(self, system_prompt: str, user_prompt: str) -> str:
        """Fill template with mock content."""
        time.sleep(self.delay)

        # Extract template content from the prompt
        template_match = re.search(r'## Template:\n(.*?)## Structured Context', user_prompt, re.DOTALL)
        if template_match:
            template = template_match.group(1).strip()
        else:
            if "## Template:" in user_prompt:
                parts = user_prompt.split("## Template:")
                template = parts[1].split("## Structured Context")[0].strip()
            else:
                template = user_prompt

        # Replace common placeholders with mock data
        filled = template
        placeholder_replacements = {
            "{STATUS}": "draft",
            "{Project Name}": "Mock Project",
            "{project_name}": "Mock Project",
            "{owner}": "mock-owner",
            "{repo}": "mock-repo",
            "{repo_url}": "https://github.com/mock-owner/mock-repo",
        }

        for placeholder, value in placeholder_replacements.items():
            filled = filled.replace(placeholder, value)

        # Replace remaining {PLACEHOLDER} markers
        filled = re.sub(
            r'\{[^}]+\}',
            lambda m: f"[Mock: {m.group(0).strip('{}')}]",
            filled
        )

        return filled

    def get_provider_name(self) -> str:
        return "Mock Provider (Testing)"

    def is_available(self) -> bool:
        return True

    def _detect_languages(self, content: str) -> list:
        """Detect programming languages from content."""
        langs = []
        checks = {
            "Python": ["import ", "def ", "class ", "from ", ".py"],
            "JavaScript": ["const ", "let ", "var ", "function ", "require(", "import {"],
            "TypeScript": [": string", ": number", "interface ", ".ts"],
            "Java": ["public class", "private ", "void ", ".java"],
            "Go": ["func ", "package ", "import (", ".go"],
            "Rust": ["fn ", "pub ", "use ", "mod ", ".rs"],
            "C#": ["namespace ", "using ", "public class", ".cs"],
            "HTML": ["<!DOCTYPE", "<html", "<div", ".html"],
            "CSS": ["{color:", "margin:", "padding:", ".css"],
            "SQL": ["CREATE TABLE", "SELECT ", "INSERT ", "ALTER TABLE"],
            "Docker": ["FROM ", "WORKDIR ", "COPY ", "RUN ", "EXPOSE"],
            "YAML": ["name:", "on:", "jobs:", "steps:"],
        }
        for lang, patterns in checks.items():
            if any(p in content for p in patterns):
                langs.append(lang)
        return langs or ["Unknown"]

    def _detect_endpoints(self, content: str) -> list:
        """Detect API endpoints from content."""
        endpoints = []
        patterns = [
            (r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)', 'Python/FastAPI'),
            (r'router\.(get|post|put|delete|patch)\(["\']([^"\']+)', 'Python/FastAPI'),
            (r'app\.(get|post|put|delete|patch)\(["\']([^"\']+)', 'Express'),
        ]
        for pattern, framework in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for method, path in matches[:5]:
                endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "description": f"[Mock] Endpoint detected ({framework})",
                    "source": "mock_analysis"
                })
        return endpoints

    def _detect_env_vars(self, content: str) -> list:
        """Detect environment variables from content."""
        env_vars = set()
        patterns = [
            r'os\.getenv\(["\']([A-Z_]+)',
            r'os\.environ\[["\']([A-Z_]+)',
            r'process\.env\.([A-Z_]+)',
            r'([A-Z_]{3,})=',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content)
            env_vars.update(matches[:10])
        return list(env_vars)

    def _detect_tables(self, content: str) -> list:
        """Detect database tables from content."""
        tables = []
        patterns = [
            r'class\s+(\w+)\(.*(?:Base|Model)',
            r'CREATE\s+TABLE\s+(\w+)',
            r'__tablename__\s*=\s*["\'](\w+)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for name in matches[:5]:
                tables.append({
                    "name": name,
                    "columns": ["id", "[mock columns]"],
                    "source": "mock_analysis"
                })
        return tables
