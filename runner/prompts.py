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
PART A — CLEAN HANDLING OF UNFOUND CONTEXT (CRITICAL)
═══════════════════════════════════════════════════

A1. NEVER WRITE "[MISSING]" ANYWHERE:
    • Do NOT write `[MISSING]` or `[UNFOUND]` anywhere in tables, headings, or prose.
    • For table cells where specific metadata (such as Required/Req, Constraints, Evidence,
      or Default) is not explicitly defined in code: use clean, professional placeholders
      like `-`, `Optional`, `None`, `N/A`, or infer a reasonable standard value.
    • If an entire feature is not applicable to this project (e.g. Docker in a pure library,
      SQL tables in a static site), write a natural, clean summary sentence explaining that
      the project does not require or utilize that component.

A2. REMOVE EMPTY TABLES COMPLETELY:
    • If a template contains a Markdown table with {{#EACH}} rows but the Structured
      Context has ZERO items for that loop, DELETE the entire table (header row, separator
      row, and all placeholder rows). Do NOT output a table with only headers and no data.
    • If a template section has MULTIPLE tables and only SOME have data, keep the populated
      tables and delete only the empty ones.

A3. MERMAID DIAGRAMS — KEEP AND FILL (CRITICAL):
    • The templates contain pre-designed Mermaid diagram blocks with {{PLACEHOLDER}} markers
      inside node labels, edge labels, and participant names.
    • You MUST KEEP every Mermaid diagram and FILL the placeholders with REAL data from
      the Structured Context. The placeholder names in diagrams (e.g. {{L1_ACTOR_1}},
      {{SEQ_STEP_1}}, {{AUTH_CLIENT}}, {{MODEL_1}}) are descriptive hints — map them to
      the closest matching data from the context:
        - {{L1_ACTOR_1}}, {{L2_ACTOR}}, {{SEQ_ACTOR}} → real user roles or client types
        - {{L2_FRONTEND}}, {{L2_API}}, {{L2_DATABASE}} → real component/service names
        - {{SEQ_STEP_1}} through {{SEQ_STEP_9}} → real request/response flow steps
        - {{AUTH_CLIENT}}, {{AUTH_API}}, {{AUTH_IDP}} → real auth participants
        - {{MODEL_1}}, {{MODEL_2}} → real data model/entity names
        - {{ERR_401}}, {{ERR_403}}, {{ERR_404}} → real error descriptions
    • Preserve the Mermaid %%{init:...}%% theme configuration line exactly as-is.
    • Preserve all classDef and class lines exactly as-is.
    • ONLY delete a Mermaid block if the ENTIRE section is completely not applicable to the codebase.

A4. ZERO RAW PLACEHOLDERS:
    • After filling, the final document must contain ZERO raw template tags
      (no {{PLACEHOLDER}}, no {PLACEHOLDER}, no {{#EACH}}...{{/EACH}} blocks).
    • For Mermaid diagram placeholders: fill them with real data (rule A3).
    • For table cells without data: use `-` or `N/A` (never write `[MISSING]`).

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

C1. STRICT TEMPLATE STRUCTURE: Follow the exact structure, layout, and section hierarchy
    of the provided template verbatim. Start directly with the template's # Title and
    ### {{PROJECT_NAME}}. Do NOT insert any shields.io badges, metadata badges, or headers
    unless they exist in the template itself.
C2. KEEP all main section headings (## headings) in order. Do NOT add, remove, or rename
    main headings.
C3. MANDATORY 10-LINE SECTION DESCRIPTIONS: Under EVERY ## heading (and major sub-sections),
    write a rich, formal, and comprehensive 10-line introductory description/narrative
    explaining:
      1. What this part of the system or architecture is and its primary responsibility.
      2. Why it matters to the application, business logic, and overall workflow.
      3. How it operates in runtime and interacts with surrounding components.
      4. Key engineering decisions, protocols, state management, or security guarantees.
    Write this 10-line narrative directly beneath each heading before any tables or diagrams.
    (For sections marked [NOT APPLICABLE] or [MISSING], write 2–3 concise sentences explaining why).
C4. Preserve ALL Mermaid diagrams with their %%{init:...}%% theme lines. Fill every
    placeholder inside diagrams with real project data from the Structured Context.
C5. Use clean tables over prose for any enumerable data (components, endpoints,
    features, dependencies) — but only when data exists to populate them.
C6. Cross-reference other documents by name in italics, e.g., "see *Deployment-Guide.md,
    section 6*".
C7. Voice: formal, clear, authoritative, and direct.

═══════════════════════════════════════════════════
PART D — OUTPUT
═══════════════════════════════════════════════════

D1. Output the completed Markdown document ONLY — no preamble, no closing remarks,
    no wrapping in outer code fences.
D2. Delete every <!-- FILL: --> and <!-- EXAMPLE --> comment. Keep <!-- ANCHOR: --> comments.
D3. Follow the template file faithfully without inventing extra visual decorations."""


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

## Template Rules:
- STRICT TEMPLATE FIDELITY: Follow the exact structure, layout, headings, and formatting of the provided Template below.
- Start directly with the template's title and project name as defined in the template. Do NOT add any shields.io badges or decorative banners.
- Keep all ## headings in order. Never add, remove, or rename them.
- MANDATORY 10-LINE SECTION DESCRIPTIONS: Under EVERY ## heading, write a rich, formal, and comprehensive 10-line introductory narrative describing: (1) what this section covers and its core responsibility, (2) why it is critical to the business logic/workflow, (3) how it functions in runtime and communicates with other parts of the system, and (4) key engineering decisions and architecture trade-offs. Write this narrative right below the ## heading before any tables or diagrams.
- CLEAN TABLE DATA (NEVER WRITE "[MISSING]"): Do NOT write `[MISSING]` anywhere in table cells or text. When optional attributes (such as Req, Constraints, Evidence, Notes) are not explicitly specified in the codebase, output a clean default such as `-`, `Optional`, `N/A`, or infer a sensible standard.
- REMOVE EMPTY TABLES: If a {{{{#EACH}}}} loop has ZERO items, delete the ENTIRE table
  (headers + separator + placeholder rows). Never output header-only tables.

## CRITICAL — MERMAID DIAGRAMS (DO NOT DELETE):
- The template contains pre-designed Mermaid diagram blocks with {{{{PLACEHOLDER}}}} markers
  inside node labels, edge labels, and participant names.
- You MUST KEEP every Mermaid diagram and REPLACE all placeholders with REAL data from
  the Structured Context. Map placeholder names to the closest matching real data:
    • Architecture diagrams: map {{{{L1_ACTOR_1}}}}, {{{{L2_FRONTEND}}}}, {{{{L2_API}}}},
      {{{{L2_DATABASE}}}} etc. to real component/service/actor names from ARCHITECTURE and TECH_STACK.
    • Sequence diagrams: map {{{{SEQ_STEP_1}}}} through {{{{SEQ_STEP_9}}}} to the real
      request/response flow derived from API_ENDPOINTS and ARCHITECTURE.
    • Auth diagrams: map {{{{AUTH_CLIENT}}}}, {{{{AUTH_API}}}}, {{{{AUTH_IDP}}}} to real
      auth participants from AUTHENTICATION.
    • Class/model diagrams: map {{{{MODEL_1}}}}, {{{{MODEL_2}}}} to real entity/model names
      from DATABASE or MODULES.
    • Error flow diagrams: map {{{{ERR_401}}}}, {{{{ERR_403}}}} etc. to real error descriptions.
- Preserve the Mermaid %%{{{{init:...}}}}%% theme configuration line EXACTLY as-is.
- Preserve all classDef and class lines EXACTLY as-is.
- ONLY delete a Mermaid block if its ENTIRE parent section is [NOT APPLICABLE].

- ZERO LEFTOVER PLACEHOLDERS: The final document must contain no raw {{{{PLACEHOLDER}}}},
  {{{{#EACH}}}}, or {{{{/EACH}}}} markers. Diagram placeholders must be filled with real data.
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
Generate the completed Markdown document according to the rules above:
remove empty tables, fill ALL Mermaid diagram placeholders with real project data,
use clean '-' or 'N/A' defaults for undefined table cells (NEVER write '[MISSING]'),
and ensure zero raw placeholders remain. Keep all headings, formatting, and Mermaid themes intact."""


# =====================================================================
# TEMPLATE CONTEXT DELIVERY
# =====================================================================
# Every template now receives the FULL Structured Context so the LLM
# has access to all extracted knowledge (ARCHITECTURE, SECURITY,
# API_ENDPOINTS, CONFIGURATION, DATABASE, etc.) regardless of which
# template is being filled.  This eliminates [MISSING] markers caused
# by context sections being filtered out.
#
# The original per-template filtering was an optimisation for very large
# contexts; with the current chunking settings it is unnecessary and
# was actively causing incomplete documents.
# =====================================================================


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
    """Return the FULL Structured Context for every template.

    Previously this filtered by TEMPLATE_CONTEXT_MAP, but that caused
    [MISSING] markers when templates needed data from excluded sections.
    All templates now receive the complete context.
    """
    return full_context