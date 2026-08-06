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
1. A TEMPLATE with {PLACEHOLDER} markers, {{#EACH}} loops, and specific structural rules.
2. A STRUCTURED CONTEXT containing verified, source-traced facts about the project.
3. Template rules from the 00-README-How-To-Use.md guide.

═══════════════════════════════════════════════════
PART A — HANDLING MISSING / UNFOUND CONTEXT (HIGHEST PRIORITY)
═══════════════════════════════════════════════════

A1. CONTEXT NOT FOUND — TIERED RESPONSE:
    When the Structured Context does NOT contain information for a template section:
    • If the feature is IRRELEVANT to this project type (e.g. Docker in a pure library,
      SQL tables in a static site), write `[NOT APPLICABLE] — <one-line reason>` under
      the section heading and remove ALL tables, diagrams, and code blocks in that section.
    • If the feature COULD exist but was not found in the repository scan, write
      `[MISSING] — searched <what was searched>; not found in repository` and similarly
      remove all tables, diagrams, and code blocks from that section.
    • In BOTH cases, keep the section heading (## heading) itself — never delete headings.

A2. REMOVE EMPTY TABLES COMPLETELY:
    • If a template contains a Markdown table with {{#EACH}} rows but the Structured
      Context has ZERO items for that loop, DELETE the entire table (header row, separator
      row, and all placeholder rows). Do NOT output a table with only headers and no data.
    • If a template section has MULTIPLE tables and only SOME have data, keep the populated
      tables and delete only the empty ones.

A3. REMOVE EMPTY DIAGRAMS:
    • If a Mermaid diagram's placeholders cannot be filled because the context lacks the
      required data (e.g., no lifecycle states, no read/write paths), DELETE the entire
      ```mermaid ... ``` block and its introductory sentence.
    • If a diagram CAN be partially filled with real data, keep it and fill what you can.

A4. REMOVE UNFILLED PLACEHOLDERS:
    • After filling, the final document must contain ZERO raw placeholder markers
      (no {{PLACEHOLDER}}, no {PLACEHOLDER}, no {{#EACH}}...{{/EACH}} blocks).
    • Any placeholder that cannot be resolved → apply rule A1 (mark [NOT APPLICABLE]
      or [MISSING]) and remove the surrounding structure.

═══════════════════════════════════════════════════
PART B — CONTENT INTEGRITY (NEVER VIOLATE)
═══════════════════════════════════════════════════

B1. NEVER hallucinate or invent features, endpoints, tables, architecture, or data
    not present in the Structured Context. If it's not in the context, it does not exist.
B2. Replace {PLACEHOLDER} markers ONLY with real, verified data from the Structured Context.
B3. Mark anything you must infer from code patterns as *(inferred)* in italics.
B4. Cite source files where possible: `path/to/file.ext:L12-L34`.
B5. Secret names only — never output secret values.

═══════════════════════════════════════════════════
PART C — STRUCTURE & FORMATTING
═══════════════════════════════════════════════════

C1. KEEP all main section headings (## headings) in order. Do NOT add, remove, or rename
    main headings.
C2. LAYMAN SECTION DESCRIPTIONS (MANDATORY): Under EVERY ## heading that has content,
    write a rich, formal introductory paragraph (5–10 lines) explaining the topic in
    plain, layman-understandable language — what this part of the system is, why it
    matters, and how it works, so non-technical stakeholders can understand it.
    For sections marked [NOT APPLICABLE] or [MISSING], write 1–2 sentences explaining
    why instead of the full paragraph.
C3. Badges are MANDATORY on the first line, using the exact pattern from the template.
C4. Preserve the Mermaid %%{init:...}%% theme line for any diagrams that remain.
C5. Use clean tables over prose for any enumerable data (components, endpoints,
    features, dependencies) — but only when data exists to populate them.
C6. Cross-reference other documents by name in italics, e.g., "see *Deployment-Guide.md,
    section 6*".
C7. Voice: formal, clear, human-understandable, and direct.

═══════════════════════════════════════════════════
PART D — OUTPUT
═══════════════════════════════════════════════════

D1. Output the completed Markdown document ONLY — no preamble, no closing remarks,
    no wrapping in code fences.
D2. Delete every <!-- FILL: --> and <!-- EXAMPLE --> comment. Keep <!-- ANCHOR: --> comments.
D3. Target 200–250 lines per document. Cut filler and redundant prose, not substance."""


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
- Keep all ## headings in order. Never add, remove, or rename them.
- MANDATORY LAYMAN DESCRIPTIONS: Under every ## heading with data, write a rich, formal
  introductory paragraph (8–12 lines) in plain, layman-understandable language.
  For sections marked [NOT APPLICABLE] or [MISSING], write 1–2 explanatory sentences instead.
- MISSING CONTEXT — TIERED HANDLING:
  → Feature irrelevant to this project: `[NOT APPLICABLE] — <reason>` + delete all tables/diagrams in that section.
  → Feature possible but not found: `[MISSING] — searched <what>; not found in repository` + delete tables/diagrams.
  → In both cases, keep the ## heading — never delete it.
- REMOVE EMPTY TABLES: If a {{{{#EACH}}}} loop has ZERO items, delete the ENTIRE table
  (headers + separator + placeholder rows). Never output header-only tables.
- REMOVE EMPTY DIAGRAMS: If a Mermaid block's placeholders can't be filled, delete the
  entire ```mermaid ... ``` block and its introductory sentence.
- ZERO LEFTOVER PLACEHOLDERS: The final document must contain no raw {{{{PLACEHOLDER}}}},
  {{{{#EACH}}}}, or {{{{/EACH}}}} markers.
- Badges are MANDATORY on the first line.
- Color palette: Primary #2E74B5, Secondary #1F4D78, Accent #0563C1, Tertiary #EAF1FA.
- Preserve the Mermaid %%{{init:...}}%% theme line for diagrams that remain.
- Tables for enumerable facts (only when data exists); prose for reasoning.
- Cross-reference other docs by name in italics instead of duplicating content.
- Voice: formal, clear, human-understandable. Cite sources as `path/to/file:L##`.
- Delete <!-- FILL: --> and <!-- EXAMPLE --> comments. Keep <!-- ANCHOR: --> comments.

## Project Info:
- Project Name: {project_name}
- Repository URL: {repo_url}

## Template:
{template_content}

## Structured Context (use ONLY this data — do not invent):
{structured_context}

## Output:
Generate the completed Markdown document. Apply the tiered missing-context rules above:
remove empty tables, remove unfillable diagrams, mark inapplicable or missing sections,
and ensure zero raw placeholders remain. Keep all headings, formatting, and Mermaid themes intact."""


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
