"""
Professional LLM Prompts for the AI Documentation Generation Platform.

This module contains all system prompts, chunk analysis prompts,
and template filling prompts used throughout the pipeline.

Design principles:
  - Every prompt is self-contained and production-ready.
  - Chunk analysis extracts structured JSON — no prose, no hallucination.
  - Template filling preserves template structure exactly.
  - Source traceability is enforced — every fact must cite its source file.
  - Missing information is explicitly flagged, never invented.
"""


# =====================================================================
# SYSTEM PROMPTS
# =====================================================================

CHUNK_ANALYSIS_SYSTEM_PROMPT = """You are a Principal Software Architect with 20+ years of experience analyzing enterprise codebases.

Your task is to analyze a CODE CHUNK from a software repository and extract structured knowledge.

CRITICAL RULES:
1. Return ONLY valid JSON matching the exact schema provided. No markdown, no commentary, no preamble.
2. Be precise and factual. Only report what you can directly observe in the code.
3. For every piece of knowledge, include the SOURCE FILE PATH where you found it.
4. If something is unclear or cannot be determined from this chunk alone, put it in "unknown_areas".
5. NEVER invent or hallucinate features, endpoints, tables, or architecture that isn't present in the code.
6. If a field has no relevant information in this chunk, use an empty string "", empty array [], or null.
7. Classify code patterns accurately — do not confuse controllers with services, or models with utilities.
8. Note security concerns, potential issues, and notable design patterns when you see them.

You are analyzing ONE chunk out of several. Other chunks will cover other parts of the repository. Focus only on what THIS chunk contains."""


TEMPLATE_FILLING_SYSTEM_PROMPT = """You are a Senior Technical Writer with expertise in producing professional software documentation for enterprise teams.

You will receive:
1. A TEMPLATE with {PLACEHOLDER} markers and specific structural rules.
2. A STRUCTURED CONTEXT containing verified, source-traced facts about the project.
3. Template rules from the 00-README-How-To-Use.md guide.

CRITICAL RULES:
1. KEEP all main section headings (## headings), badges, and Mermaid theme styling provided.
2. Do NOT add new main sections or rename main headings.
3. EXCELLENT LAYMAN SECTION DESCRIPTIONS (MANDATORY): Under EVERY main section heading (## heading) in the template, write a rich, formal, and thorough introductory paragraph of approximately 5 to 10 lines. This description must explain the heading topic exceptionally well in simple, human-accessible, layman-understandable language — detailing what this part of the system is, why it is important to the application, and how it works so non-technical stakeholders can easily understand it.
4. REMOVE UNFOUND / MISSING CONTENT: If specific content, tables, diagrams, or subsections requested by placeholders in the template are NOT found in the repository (e.g. no Docker containers, no SQL tables, no CI/CD pipeline configs), REMOVE those empty placeholder tables, unused code blocks, or missing sub-diagrams completely from the final document. Do NOT leave empty tables or placeholder markers for missing features. Simply note cleanly in the section description that the feature is not implemented/present in this repository and remove the empty tables/diagrams.
5. Replace ONLY the {PLACEHOLDER} markers with real, verified information from the Structured Context.
6. Badges are MANDATORY on the first line, using the exact pattern from the template.
7. The Mermaid init line with theme variables must be preserved for any diagrams that remain.
8. NEVER hallucinate or invent features, endpoints, tables, or architecture not present in the repository context.
9. Mark anything you must infer from code patterns as "(inferred)" in italics.
10. Use clean tables over prose for any enumerable data (components, endpoints, features, dependencies).
11. Cross-reference other documents by name in italics, e.g., "see *Deployment-Guide.md, section 6*".
12. Voice: formal, clear, human-understandable, and direct. Combine accessible, educational section introductions with precise, clean technical facts.
13. Output the completed Markdown document ONLY — no preamble, no closing remarks, no wrapping in code fences."""


# =====================================================================
# CHUNK ANALYSIS PROMPT
# =====================================================================

CHUNK_ANALYSIS_PROMPT = """Analyze the following code chunk and extract structured knowledge.

## Repository Info
- Project Name: {project_name}
- Repository URL: {repo_url}
- Chunk Number: {chunk_number} of {total_chunks}
- Chunk Category: {chunk_category}
- Files in this chunk: {file_list}

## Required Output Schema (return ONLY this JSON structure):

{{
  "project_summary": "Brief summary of what this chunk reveals about the project (1-2 sentences)",
  "tech_stack": ["List of technologies, frameworks, languages detected in this chunk"],
  "architecture_notes": "Any architectural patterns, design decisions, or structural observations",
  "database_tables": [
    {{
      "name": "table_name",
      "columns": ["col1", "col2"],
      "source": "path/to/file.py"
    }}
  ],
  "api_endpoints": [
    {{
      "method": "GET/POST/PUT/DELETE",
      "path": "/api/endpoint",
      "description": "What it does",
      "source": "path/to/file.py"
    }}
  ],
  "authentication": {{
    "type": "JWT/OAuth/API Key/None/Unknown",
    "details": "Description of auth mechanism",
    "source": "path/to/file.py"
  }},
  "configuration": {{
    "env_vars": ["ENV_VAR_1", "ENV_VAR_2"],
    "config_files": ["path/to/config.py"],
    "source": ["path/to/file1.py", "path/to/file2.py"]
  }},
  "business_logic": "Key business rules, validation logic, or domain-specific behavior observed",
  "dependencies": {{
    "runtime": ["package1", "package2"],
    "dev": ["dev-package1"],
    "source": "requirements.txt or package.json path"
  }},
  "folder_structure_notes": "Notable observations about how the code is organized",
  "security_notes": "Any security-related observations (auth, encryption, input validation, etc.)",
  "deployment_notes": "Docker, CI/CD, deployment configuration observed",
  "ci_cd_notes": "CI/CD pipeline details if found (GitHub Actions, Azure Pipelines, etc.)",
  "docker_notes": "Docker/container configuration details",
  "coding_patterns": "Notable design patterns, naming conventions, or code style observations",
  "missing_features": "Features that seem incomplete, TODO comments, or gaps in implementation",
  "assumptions": "Any assumptions you must make about unclear code",
  "unknown_areas": "Things that cannot be determined from this chunk alone",
  "source_files": ["List of all file paths in this chunk that contributed knowledge"]
}}

## Code Chunk:

{chunk_content}"""


# =====================================================================
# CONTEXT CONSOLIDATION PROMPT
# =====================================================================

CONTEXT_CONSOLIDATION_PROMPT = """You are a Principal Software Architect. You have received {num_analyses} individual chunk analyses from a repository scan.

Your task is to CONSOLIDATE these into a single, coherent Structured Context document.

RULES:
1. Merge duplicate information — if multiple chunks report the same technology, endpoint, or table, keep it once.
2. Resolve conflicts — if chunks disagree, use the one with more specific evidence and note the conflict.
3. Preserve ALL source traceability — every fact must retain its source file path(s).
4. Organize into clear sections matching the documentation templates.
5. Return ONLY valid JSON.

## Individual Chunk Analyses:

{chunk_analyses}

## Required Output Schema:

{{
  "SYSTEM_OVERVIEW": {{
    "description": "Complete project description synthesized from all chunks",
    "project_type": "web app / API / CLI / library / etc.",
    "sources": ["file1.py", "file2.py"]
  }},
  "TECH_STACK": {{
    "languages": ["Python", "JavaScript"],
    "frameworks": ["FastAPI", "React"],
    "databases": ["PostgreSQL"],
    "other_tools": ["Docker", "Redis"],
    "sources": ["requirements.txt", "package.json"]
  }},
  "ARCHITECTURE": {{
    "pattern": "Monolith / Microservices / Serverless / etc.",
    "components": [
      {{"name": "Component Name", "responsibility": "What it does", "source": "path/to/file"}}
    ],
    "data_flow": "How data moves through the system",
    "sources": ["file1.py", "file2.py"]
  }},
  "DATABASE": {{
    "engine": "PostgreSQL / SQLite / MongoDB / None",
    "tables": [
      {{"name": "table_name", "columns": ["col1", "col2"], "source": "models.py"}}
    ],
    "relationships": "Description of table relationships",
    "sources": ["models.py", "schema.sql"]
  }},
  "API_ENDPOINTS": {{
    "endpoints": [
      {{"method": "GET", "path": "/api/users", "description": "List users", "source": "routes.py"}}
    ],
    "authentication": "How APIs are authenticated",
    "sources": ["routes.py", "auth.py"]
  }},
  "AUTHENTICATION": {{
    "type": "JWT / OAuth / API Key / None",
    "details": "How authentication works",
    "sources": ["auth.py"]
  }},
  "CONFIGURATION": {{
    "env_vars": ["DATABASE_URL", "API_KEY"],
    "config_files": ["config.py", ".env.example"],
    "sources": ["config.py"]
  }},
  "ENV_VARIABLES": {{
    "variables": [
      {{"name": "DATABASE_URL", "purpose": "Database connection string", "required": true}}
    ],
    "sources": [".env.example", "config.py"]
  }},
  "MODULES": {{
    "modules": [
      {{"name": "auth", "purpose": "Authentication and authorization", "files": ["auth.py", "jwt.py"]}}
    ],
    "sources": ["various"]
  }},
  "SERVICES": {{
    "services": [
      {{"name": "UserService", "purpose": "User management", "source": "services/user.py"}}
    ],
    "sources": ["services/"]
  }},
  "DEPENDENCIES": {{
    "runtime": [{{"package": "fastapi", "version": "0.115", "purpose": "Web framework"}}],
    "dev": [{{"package": "pytest", "purpose": "Testing"}}],
    "sources": ["requirements.txt"]
  }},
  "DEPLOYMENT": {{
    "method": "Docker / Manual / CI/CD",
    "details": "How the project is deployed",
    "sources": ["Dockerfile", "docker-compose.yml"]
  }},
  "DOCKER": {{
    "has_dockerfile": true,
    "has_compose": true,
    "services": ["api", "db", "worker"],
    "sources": ["Dockerfile", "docker-compose.yml"]
  }},
  "CI_CD": {{
    "platform": "GitHub Actions / Azure Pipelines / None",
    "workflows": ["build", "test", "deploy"],
    "sources": [".github/workflows/ci.yml"]
  }},
  "CODING_PATTERNS": {{
    "patterns": ["Repository pattern", "Dependency injection"],
    "conventions": "Naming conventions, code style observations",
    "sources": ["various"]
  }},
  "SECURITY": {{
    "observations": "Security-related findings",
    "concerns": "Potential security issues",
    "sources": ["auth.py", "middleware.py"]
  }},
  "BUSINESS_LOGIC": {{
    "rules": "Key business rules and domain logic",
    "sources": ["services/", "handlers/"]
  }},
  "MISSING_FEATURES": {{
    "items": ["List of incomplete or missing features"],
    "sources": ["various"]
  }},
  "ASSUMPTIONS": {{
    "items": ["List of assumptions made during analysis"],
    "sources": ["various"]
  }},
  "UNKNOWN_AREAS": {{
    "items": ["Things that could not be determined"],
    "sources": ["various"]
  }}
}}"""


# =====================================================================
# TEMPLATE FILLING PROMPTS
# =====================================================================

TEMPLATE_FILL_PROMPT = """Fill the following documentation template using the Structured Context provided.

## Template Rules (from 00-README-How-To-Use.md):
- Keep main ## headings in order.
- MANDATORY LAYMAN SECTION DESCRIPTIONS: Immediately following each ## main section heading, write a rich, formal, and clear introductory description paragraph (approx. 5 to 10 lines) in layman-understandable language explaining the heading topic, its purpose, and how it works in plain terms.
- REMOVE UNFOUND / MISSING CONTENT: If information for specific tables, diagrams, or subsections in the template is NOT found in the repository, REMOVE those empty tables, diagrams, or placeholder blocks from the final document. Do not leave empty rows, unused placeholder structures, or filler tables.
- Badges are MANDATORY on the first line.
- Color palette is fixed: Primary #2E74B5, Secondary #1F4D78, Accent #0563C1, Tertiary #EAF1FA.
- Every remaining Mermaid diagram must start with the init line preserving these theme colors.
- Use clean tables over prose for anything enumerable.
- Cross-reference other docs by name in italics instead of duplicating content.
- Voice: formal, clear, human-understandable explanations for section intros paired with precise technical facts in tables and diagrams.

## Project Info:
- Project Name: {project_name}
- Repository URL: {repo_url}

## Template:
{template_content}

## Structured Context (use ONLY this data):
{structured_context}

## Output:
Generate the completed Markdown document. Under every ## heading, include the formal, layman-accessible 5-10 line section description paragraph. Replace all {{PLACEHOLDER}} markers with real data from the Structured Context, and REMOVE any tables, diagrams, or blocks whose content is not found in the repository. Keep all formatting, structure, and Mermaid themes intact."""


# =====================================================================
# SPECIFIC TEMPLATE CONTEXT MAPPINGS
# =====================================================================
# Each template receives only the context sections it needs.

TEMPLATE_CONTEXT_MAP = {
    "PRD.md": [
        "SYSTEM_OVERVIEW", "MODULES", "BUSINESS_LOGIC",
        "DEPENDENCIES", "MISSING_FEATURES", "ASSUMPTIONS"
    ],
    "Architecture Design.md": [
        "SYSTEM_OVERVIEW", "ARCHITECTURE", "MODULES",
        "SERVICES", "TECH_STACK", "CODING_PATTERNS"
    ],
    "Database Design.md": [
        "DATABASE", "MODULES", "CONFIGURATION", "ARCHITECTURE"
    ],
    "API Specification.md": [
        "API_ENDPOINTS", "AUTHENTICATION", "MODULES",
        "CONFIGURATION", "TECH_STACK"
    ],
    "Deployment Guide.md": [
        "DEPLOYMENT", "DOCKER", "CI_CD",
        "CONFIGURATION", "ENV_VARIABLES", "DEPENDENCIES"
    ],
    "Review and TODO.md": [
        "MISSING_FEATURES", "SECURITY", "ASSUMPTIONS",
        "UNKNOWN_AREAS", "CODING_PATTERNS"
    ],
}


# =====================================================================
# SEMANTIC RETRIEVAL QUERIES FOR RAG (Stage 3.5 → Stage 6)
# =====================================================================
# Each template uses a natural-language query to find the most relevant
# raw code chunks via cosine similarity before the LLM call.

TEMPLATE_SEMANTIC_QUERIES = {
    "PRD.md": (
        "product requirements features business logic user stories goals objectives scope"
    ),
    "Architecture Design.md": (
        "system architecture components services modules layers data flow design patterns"
        " microservices monolith dependency injection repository pattern tech stack frameworks libraries"
    ),
    "Database Design.md": (
        "database models tables schemas ORM migrations columns relationships SQL foreign key"
        " SQLAlchemy Sequelize Mongoose entity"
    ),
    "API Specification.md": (
        "API routes endpoints controllers REST HTTP GET POST PUT DELETE request response"
        " FastAPI Express Flask handler middleware authentication JWT"
    ),
    "Deployment Guide.md": (
        "Docker Dockerfile docker-compose deployment CI CD pipeline Kubernetes Nginx"
        " environment variables production configuration cloud deploy local setup prerequisites install run start"
    ),
    "Review and TODO.md": (
        "TODO FIXME technical debt code smell missing feature incomplete security"
        " vulnerability bug improvement refactor warning"
    ),
}


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def build_chunk_analysis_prompt(
    project_name: str,
    repo_url: str,
    chunk_number: int,
    total_chunks: int,
    chunk_category: str,
    file_list: list,
    chunk_content: str,
) -> str:
    """Build the complete prompt for analyzing a single chunk."""
    return CHUNK_ANALYSIS_PROMPT.format(
        project_name=project_name,
        repo_url=repo_url,
        chunk_number=chunk_number,
        total_chunks=total_chunks,
        chunk_category=chunk_category,
        file_list=", ".join(file_list),
        chunk_content=chunk_content,
    )


def build_context_consolidation_prompt(
    num_analyses: int,
    chunk_analyses: str,
) -> str:
    """Build the prompt for consolidating chunk analyses into Structured Context."""
    return CONTEXT_CONSOLIDATION_PROMPT.format(
        num_analyses=num_analyses,
        chunk_analyses=chunk_analyses,
    )


def build_template_fill_prompt(
    project_name: str,
    repo_url: str,
    template_content: str,
    structured_context: str,
) -> str:
    """Build the prompt for filling a documentation template."""
    return TEMPLATE_FILL_PROMPT.format(
        project_name=project_name,
        repo_url=repo_url,
        template_content=template_content,
        structured_context=structured_context,
    )


def get_relevant_context_sections(template_name: str, full_context: dict) -> dict:
    """Extract only the context sections relevant to a given template."""
    relevant_keys = TEMPLATE_CONTEXT_MAP.get(template_name, list(full_context.keys()))
    return {k: v for k, v in full_context.items() if k in relevant_keys}
