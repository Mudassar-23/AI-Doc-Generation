# ✨ AI Documentation Generation Platform

> **A production-grade, enterprise-ready platform that automatically clones a software repository, analyzes it with AI, and generates a professional, source-traced documentation bundle as a downloadable ZIP file.**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Project Structure](#project-structure)
5. [Technology Stack](#technology-stack)
6. [AI Provider System](#ai-provider-system)
7. [The Pipeline (8 Stages)](#the-pipeline-8-stages)
8. [RAG-Enhanced Document Generation](#rag-enhanced-document-generation)
9. [Token Calculation & Chunking](#token-calculation--chunking)
10. [Database Models](#database-models)
11. [REST API Reference](#rest-api-reference)
12. [Generated Documentation](#generated-documentation)
13. [Installation & Setup](#installation--setup)
    - [Virtual Environment Setup](#virtual-environment-setup)
14. [Configuration Reference](#configuration-reference)
15. [Running the Platform](#running-the-platform)
16. [Docker Deployment](#docker-deployment)
17. [Running Tests](#running-tests)
18. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Documentation Generation Platform automates the creation of professional software documentation from any GitHub or Azure DevOps repository. Simply paste a repository URL (with optional Personal Access Token for private repos), select an AI provider, and the system runs a **8-stage automated pipeline** to produce 6 structured markdown documents — all packaged into a ZIP file ready for download.

The platform runs a **FIFO (First-In, First-Out) background queue**, handles multiple concurrent user requests gracefully, and intelligently chunks repositories into semantic groups before passing them to an AI model — preventing context window overflows while maintaining source traceability throughout.

**New in the latest release:** The pipeline now includes **Stage 3.5 — Vector Embeddings (RAG)**, which uses Azure OpenAI Embeddings to index all semantic chunks into a cosine similarity vector store. During document generation (Stage 6), each template retrieves its top-8 most relevant raw code snippets — giving the LLM precise source evidence alongside the consolidated structured context for higher-accuracy output.

---

## Key Features

| Feature | Details |
| :--- | :--- |
| 🤖 **Dynamic AI Fallback** | Abacus AI → Azure AI Foundry → Mock Provider (automatic cascade) |
| 📦 **8-Stage Pipeline** | Clone → Analyze → Chunk → **Embed (RAG)** → LLM → Context → Fill Templates → ZIP |
| 🔎 **RAG-Enhanced Generation** | Per-template semantic chunk retrieval using Azure OpenAI Embeddings + cosine similarity |
| 🔗 **Repo Support** | GitHub (PAT) and Azure DevOps (PAT) |
| 🧩 **Semantic Chunking** | Groups files by category, targeting ~4,000 tokens per LLM call |
| 📊 **Live Token Stats UI** | Live Stats panel shows chunk tokens and template input/output tokens in real time |
| 🗂️ **Smart File Handling** | Three-tier strategy: normal ≤700 KB, split 700 KB–3 MB, type-aware >3 MB (source code split with cap; generated/data files skipped) |
| 🛡️ **Secret Sanitization** | All PAT tokens and API keys are redacted from logs and error messages |
| 📂 **Source Traceability** | Every documented fact is tied back to a specific file path |
| 🗄️ **Dual Database** | PostgreSQL for production, automatic SQLite fallback |
| 🔒 **Windows File Safety** | Custom `safe_rmtree` handles `.git` read-only pack file locks on Windows |
| 🔁 **Step Navigation** | Full `← back` / `next →` navigation across all 4 steps (Step 1 ↔ 2 ↔ 3 ↔ 4) |
| 👁️ **Live Queue Switching** | Click any job in the Live Queue panel to view its real-time pipeline progress |
| 🗑️ **Queue Dismiss** | Users can dismiss individual jobs from the Live Queue panel (frontend-only, no DB change) |
| 🧪 **Test Suite** | End-to-end pipeline tests covering clone, fallback, and full document generation |

---

## System Architecture

```
╔═══════════════════════════════════════════════════════════════╗
║              User Browser (frontend/)                        ║
║   ai-docs-generator.html  │  CSS  │  JavaScript             ║
║   4-step wizard with ← back / next → navigation             ║
║   Live Queue: click any job to switch pipeline view          ║
╚══════════════════╦════════════════════════════════════════════╝
                   ║ HTTP Requests (REST API)
╔══════════════════╩════════════════════════════════════════════╗
║              FastAPI Backend (backend/)                      ║
║  routes/jobs.py  │  routes/health.py  │  routes/queue.py    ║
║  services/       │  schemas.py        │  models.py           ║
╚══════════════════╦════════════════════════════════════════════╝
                   ║ SQLAlchemy ORM
╔══════════════════╩════════════════════════════════════════════╗
║           Database (PostgreSQL / SQLite fallback)            ║
║  tables: jobs │ job_progress │ job_logs                      ║
╚══════════════════╦════════════════════════════════════════════╝
                   ║ FIFO Polling Queue (every 2s)
╔══════════════════╩════════════════════════════════════════════╗
║           Background Runner Daemon (runner/)                 ║
║  stage_manager.py  →  8-stage pipeline                      ║
║  [Stage 3.5] AzureEmbedder → ChunkVectorStore (RAG index)   ║
╚══════════════════╦════════════════════════════════════════════╝
                   ║ Provider Fallback Sequence
╔══════════════════╩════════════════════════════════════════════╗
║           AI Provider System (runner/providers/)             ║
║  [Abacus AI]  →  [Azure AI Foundry]  →  [Mock Provider]     ║
╚═══════════════════════════════════════════════════════════════╝
                   │
                   ▼ Azure OpenAI Embeddings (Stage 3.5)
╔═══════════════════════════════════════════════════════════════╗
║  runner/analysis/embeddings.py  —  AzureEmbedder            ║
║  runner/analysis/vector_store.py —  ChunkVectorStore         ║
║  Pure-Python cosine similarity, zero external dependencies   ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Project Structure

```
ai-documentation/
│
├── backend/                          # FastAPI REST API server
│   ├── main.py                       # App entrypoint, CORS, static file serving, lifespan startup
│   ├── config.py                     # Backend settings from .env
│   ├── database.py                   # SQLAlchemy session manager + PostgreSQL/SQLite init
│   ├── models.py                     # ORM models: Job, JobProgress, JobLog
│   ├── schemas.py                    # Pydantic request/response schemas
│   ├── requirements.txt              # FastAPI, SQLAlchemy, psycopg2, pydantic, uvicorn
│   ├── Dockerfile                    # Backend container image
│   ├── routes/
│   │   ├── jobs.py                   # POST /api/jobs, GET progress, download, retry, logs
│   │   ├── health.py                 # GET /api/health, GET /api/providers
│   │   └── queue.py                  # GET /api/queue (all active jobs)
│   └── services/
│       ├── job_service.py            # Job CRUD: create, get, update, retry
│       └── queue_service.py          # Queue position calculation
│
├── runner/                           # Background pipeline daemon
│   ├── main.py                       # FIFO polling loop, provider selection, job dispatch
│   ├── config.py                     # RunnerConfig: env vars, chunking settings, embedding config
│   ├── stage_manager.py              # Orchestrates all 8 stages (incl. Stage 3.5 embeddings)
│   ├── prompts.py                    # LLM prompts, TEMPLATE_CONTEXT_MAP, TEMPLATE_SEMANTIC_QUERIES
│   ├── requirements.txt              # SQLAlchemy, openai, requests, tiktoken, gitpython
│   ├── Dockerfile                    # Runner container image
│   │
│   ├── stages/                       # One file per pipeline stage
│   │   ├── s1_clone.py               # Git clone w/ absolute paths & Windows-safe cleanup
│   │   ├── s2_analyze.py             # File discovery, categorization, filtering
│   │   ├── s3_chunk.py               # Semantic chunking + token estimation table (UNCHANGED)
│   │   ├── s4_llm_analyze.py         # Per-chunk LLM JSON extraction
│   │   ├── s5_context_build.py       # Merge chunk analyses into Structured Context
│   │   ├── s6_template_fill.py       # Template loading + LLM fill + RAG retrieval + token stats
│   │   └── s7_package.py             # ZIP packaging + manifest
│   │
│   ├── analysis/                     # Standalone analysis utilities
│   │   ├── file_filter.py            # .gitignore parser, DEFAULT_IGNORES, file discovery
│   │   ├── file_categorizer.py       # Categorize files (Models, Controllers, CI/CD, etc.)
│   │   ├── chunk_builder.py          # estimate_tokens(), build_chunks(), format_chunk_for_prompt()
│   │   ├── context_builder.py        # LLM-based consolidation of chunk analyses
│   │   ├── embeddings.py             # [NEW] AzureEmbedder — batch embedding via Azure OpenAI
│   │   └── vector_store.py           # [NEW] ChunkVectorStore — pure-Python cosine similarity
│   │
│   ├── providers/                    # AI provider adapters
│   │   ├── base.py                   # Abstract BaseProvider interface
│   │   ├── abacus_provider.py        # Abacus AI (Claude Sonnet via HTTP API)
│   │   ├── azure_ai_provider.py      # Azure AI Foundry (OpenAI SDK, max_completion_tokens)
│   │   ├── mock_provider.py          # Offline mock with realistic template filling
│   │   └── fallback_provider.py      # Cascade: Abacus → Azure AI → Mock
│   │
│   └── tests/
│       └── test_pipeline.py          # FallbackProvider, clone, and full pipeline tests
│
├── frontend/                         # Single-page HTML/CSS/JS client
│   ├── ai-docs-generator.html        # Main UI (4-step wizard with full back/next nav)
│   ├── css/ai-docs-generator.css     # Styling (back-link, next-link, queue-row, active-job)
│   ├── js/ai-docs-generator.js       # API polling, pipeline stepper, queue job switching
│   ├── logo.png                      # Platform logo
│   ├── favicon.svg                   # ✨ Sparkles favicon
│   └── favicon.ico                   # Favicon fallback
│
├── templates/                        # 6 documentation templates (Markdown)
│   ├── 00-README-How-To-Use.md       # Template usage guide & authoring contract
│   ├── PRD.md
│   ├── Architecture Design.md
│   ├── Database Design.md
│   ├── API Specification.md
│   ├── Deployment Guide.md
│   └── Review and TODO.md
│
├── outputs/                          # Generated ZIP files (git-ignored)
├── tmp/                              # Temporary clone directories (git-ignored)
├── data/                             # SQLite database file (git-ignored)
├── venv/                             # Python virtual environment (git-ignored)
├── docker-compose.yml                # Multi-service container setup
├── run_tests.py                      # Custom test runner (no pytest required)
├── pytest.ini                        # Pytest configuration
├── requirements-dev.txt              # Dev dependencies (pytest, httpx + all above)
├── .env.example                      # Environment variable template
└── README.md                         # This file
```

---

## Technology Stack

### Backend
| Component | Technology |
| :--- | :--- |
| Web Framework | FastAPI 0.115.6 |
| ORM | SQLAlchemy 2.0.36 |
| Database | PostgreSQL 16 (SQLite fallback) |
| Validation | Pydantic v2 |
| Server | Uvicorn ≥0.28.0 |

### Runner
| Component | Technology |
| :--- | :--- |
| OpenAI SDK | `openai==1.58.1` (Azure AI Foundry + Azure Embeddings) |
| HTTP Client | `requests==2.32.3` (Abacus AI) |
| Token estimation | `tiktoken==0.8.0` |
| Git access | `gitpython==3.1.44` + subprocess `git` |
| Config | `python-dotenv==1.0.1` |
| Vector similarity | Pure Python stdlib (`math`) — zero extra deps |

### Frontend
| Component | Technology |
| :--- | :--- |
| UI | Vanilla HTML5, CSS3, JavaScript |
| Server | Served by FastAPI static file mounting |

---

## AI Provider System

The platform has a three-tier fallback AI system managed by [`runner/providers/fallback_provider.py`](file:///d:/AI%20Documentation/runner/providers/fallback_provider.py):

```
Attempt 1: Abacus AI (Claude Sonnet via Abacus AI HTTP API)
    ↓ (fails or not configured)
Attempt 2: Azure AI Foundry (OpenAI SDK, any deployed model)
    ↓ (fails or not configured)
Attempt 3: Mock Provider (offline, local template population)
```

### Provider Availability Detection
All providers filter out placeholder keys — `is_available()` returns `False` if the key contains strings like `"your-"`, `"placeholder"`, or `"here"`, ensuring the fallback chain always reaches a functional provider.

### Azure AI Parameter Compatibility
`AzureAIProvider` supports both modern models (like `gpt-4o`, `gpt-5.x`) using `max_completion_tokens` and legacy models using `max_tokens`, with automatic detection and retry on parameter error.

### Mock Provider
The offline `MockProvider` provides realistic documentation output by parsing the template structure and replacing placeholder values — useful for testing without any API keys.

---

## The Pipeline (8 Stages)

Each job submitted to the platform executes all stages sequentially, orchestrated by [`runner/stage_manager.py`](file:///d:/AI%20Documentation/runner/stage_manager.py).

```
Stage 1  →  Clone Repository
Stage 2  →  Analyze Codebase
Stage 3  →  Build Semantic Chunks          ← unchanged
Stage 3.5→  Compute Embeddings (RAG)       ← NEW — skipped gracefully if not configured
Stage 4  →  AI Chunk Analysis (LLM)
Stage 5  →  Build Structured Context
Stage 6  →  Fill Templates (RAG-enhanced)  ← top-8 chunks retrieved per document
Stage 7  →  Package ZIP
```

### Stage 1 — Clone (`s1_clone.py`)
- Constructs **absolute paths** for `temp_dir` and `repo_dir` to prevent Windows path nesting bugs.
- Runs `git clone --depth 1 <repo_url> <absolute_repo_dir>` via subprocess.
- Injects a PAT token into the URL (e.g. `https://token@github.com/org/repo`) for private repos.
- Verifies the destination directory exists after cloning.
- Uses `safe_rmtree()` for cleanup: walks the directory bottom-up, calls `os.chmod(S_IWRITE)` before each unlink to handle Windows `.git/objects/pack/*.idx` read-only lock files.

### Stage 2 — Analyze (`s2_analyze.py`)
- Discovers all files in the cloned repository using `discover_files()` from `file_filter.py`.
- Skips binary files, media, archives, lock files, compiled artifacts, and `.git` directories using `DEFAULT_IGNORES` + `.gitignore` parsing.
- Categorizes each remaining file (Models/Database, Controllers/Routes, Configuration, CI/CD, Services, Tests, etc.) using `file_categorizer.py`.
- Applies the **three-tier file handling strategy** (see [Token Calculation & Chunking](#token-calculation--chunking)).
- Returns a summary: `X total, Y analyzed, Z skipped`.

### Stage 3 — Chunk (`s3_chunk.py`)
- Groups analyzed files into semantic batches by category, sorted by processing priority (Configuration → Models → Services → Controllers → ...).
- Targets ~4,000 tokens per chunk (configurable via `TARGET_CHUNK_TOKENS`, maximum ~5,000 tokens).
- Files exceeding 8,000 tokens are processed in full without truncation (token count printed).
- Prints a formatted token estimation table to the console:
```text
============================================================
           SEMANTIC CHUNKING & TOKEN ESTIMATION
============================================================
Chunk #1 | Category: Configuration | Estimated Tokens: 1200 | Lines: 85
  - config.py
  - .env.example
------------------------------------------------------------
Total Chunks: 7 | Total Estimated Tokens: 24945
============================================================
```

### Stage 3.5 — Compute Embeddings [`runner/analysis/embeddings.py`] ⭐ NEW
- Runs immediately after Stage 3 — **does not modify Stage 3's output**.
- `AzureEmbedder` calls the Azure OpenAI Embeddings API (`text-embedding-ada-002` or any deployment) in batches of 16, with automatic retry on rate limits.
- Each chunk dict receives an `"embedding"` key (a float vector).
- `ChunkVectorStore` indexes all embedded chunks, pre-normalising vectors for O(n) cosine similarity at query time.
- **Graceful degradation**: if `AZURE_EMBEDDING_ENDPOINT` / `AZURE_EMBEDDING_DEPLOYMENT` / `AZURE_AI_API_KEY` are missing or the API call fails, the stage is logged as skipped and the pipeline continues normally — Stage 6 falls back to the full structured-context approach without any crash.

### Stage 4 — LLM Analysis (`s4_llm_analyze.py`)
- Sends each chunk to the LLM provider with a structured JSON extraction prompt.
- Extracts: project summary, tech stack, architecture notes, database tables, API endpoints, authentication, configuration, dependencies, deployment notes, security observations, missing features, and source file paths.
- Parses the LLM JSON response (with fallback for markdown code-fence wrapped responses).

### Stage 5 — Context Building (`s5_context_build.py`)
- Consolidates all individual chunk analyses into a single unified `Structured Context` JSON.
- Deduplicates merged tech stack entries, database tables, and API endpoints.
- Retains source file traceability for every piece of knowledge.

### Stage 6 — Template Filling (`s6_template_fill.py`) — RAG-enhanced
- Loads each of the 8 template `.md` files from the `templates/` directory.
- Maps relevant context sections to each template via `TEMPLATE_CONTEXT_MAP`.
- **If vector store is built**: embeds a per-template semantic query (from `TEMPLATE_SEMANTIC_QUERIES`) and retrieves the top-8 most relevant raw code chunks; appends them as `## Relevant Code Snippets` in the prompt.
- Calls the LLM to replace `{PLACEHOLDER}` markers in each template with real information.
- Prints a full document generation token statistics table:
```text
============================================================
         DOCUMENT GENERATION & TOKEN STATISTICS
         [RAG ACTIVE — semantic chunk retrieval enabled]
============================================================
  [RAG] Architecture-Design.md: 8 chunks retrieved
  [RAG] API-Specification.md: 8 chunks retrieved
  ...
Document: PRD.md                    | Input Tokens: 3764  | Output Tokens: 1355
Document: Architecture-Design.md    | Input Tokens: 4210  | Output Tokens: 1421
------------------------------------------------------------
Total Templates: 8            | Total Input: 22918 | Total Output: 9140
============================================================
```

### Stage 7 — Package (`s7_package.py`)
- Assembles all 8 generated documents into a ZIP file.
- Includes an `index.json` manifest listing all documents with their names and sizes.
- Saves the ZIP to `./outputs/<project-name>-docs-job<id>.zip`.
- Records the path in the database for download via API.

---

## RAG-Enhanced Document Generation

The embedding system adds a **Retrieval-Augmented Generation (RAG)** layer to Stage 6 without replacing any existing pipeline components.

### How It Works

```
Stage 3: chunks = [{category, file_paths, content, estimated_tokens}, ...]
                        │
Stage 3.5:   AzureEmbedder.embed_chunks(chunks)
             → chunks[i]["embedding"] = [float, float, ...]   (1536-dim vector)
             ChunkVectorStore.build(chunks)
             → normalised vectors stored in memory
                        │
              (vector_store passed to Stage 6)
                        │
Stage 6:  for each template:
             query = TEMPLATE_SEMANTIC_QUERIES[template_name]
             query_vec = AzureEmbedder.embed_texts([query])
             top_chunks = ChunkVectorStore.search(query_vec, top_k=8)
             prompt += "## Relevant Code Snippets\n" + top_chunks
             → LLM call with enriched prompt
```

### Per-Template Retrieval Queries

| Document | Semantic Query Used |
| :--- | :--- |
| `PRD.md` | product requirements features business logic user stories goals |
| `Architecture-Design.md` | system architecture components services modules layers data flow |
| `Database-Design.md` | database models tables schemas ORM migrations SQL foreign key |
| `API-Specification.md` | API routes endpoints controllers REST HTTP GET POST PUT DELETE |
| `Deployment-Guide.md` | Docker Dockerfile docker-compose deployment CI CD pipeline Nginx |
| `Run-Locally.md` | local development setup prerequisites install dependencies run start |
| `Stack-and-Techniques.md` | tech stack frameworks libraries languages tools packages versions |
| `Review-and-TODO.md` | TODO FIXME technical debt missing feature incomplete security vulnerability |

### Configuration

Add these to your `.env` (the API key is the same as `AZURE_AI_API_KEY`):

```ini
# Azure Embeddings — uses the same API key as AZURE_AI_API_KEY
AZURE_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/openai/v1
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

Leave these blank to run without embeddings — the pipeline degrades gracefully.

---

## Token Calculation & Chunking

The platform uses a character-based token estimation (no external tokenizer call required):

```python
# From runner/config.py
TOKEN_CHAR_RATIO = 4    # ~4 characters = 1 token

# From runner/analysis/chunk_builder.py
def estimate_tokens(text: str) -> int:
    return len(text) // RunnerConfig.TOKEN_CHAR_RATIO
```

**Key Limits:**

| Setting | Value | Effect |
| :--- | :--- | :--- |
| `TARGET_CHUNK_TOKENS` | 4,000 | Target tokens per chunk sent to LLM |
| `MAX_CHUNK_TOKENS` | 5,000 | Maximum tokens per chunk (hard limit per subchunk) |
| `MAX_FILE_TOKENS` | 8,000 | Token threshold for printing large-file token warning |
| `TOKEN_CHAR_RATIO` | 4 | Characters per token (approximation) |
| `LARGE_SOURCE_FILE_MAX_TOKENS` | 40,000 | Token cap for >3 MB source-code files (env-overridable) |

### Three-Tier File Handling Strategy

Every file discovered in the repository passes through `evaluate_file_size()` in [`file_filter.py`](file:///d:/AI%20Documentation/runner/analysis/file_filter.py) before being handed to the chunk builder:

| File Size | Action |
| :--- | :--- |
| **≤ 700 KB** | Analyze normally — file goes into the standard category-based chunk packing |
| **700 KB – 3 MB** | `chunk_internally` — split into 4,000–5,000 token subchunks, no token cap |
| **> 3 MB — generated / data file** | **Skip** — detected by extension (`.json`, `.csv`, `.xml`, `.ipynb`, `.pkl`, `.min.js`, etc.) or unknown extension |
| **> 3 MB — source code file** | `large_source` — split into 4,000–5,000 token subchunks, capped at `LARGE_SOURCE_FILE_MAX_TOKENS` (default 40,000). Subchunks beyond the cap are dropped with a `[WARN]` log |

The `is_generated_or_data_file()` classifier distinguishes the two >3 MB cases:
- **Data/generated** → extension in `_GENERATED_OR_DATA_EXTENSIONS` (JSON, CSV, Parquet, pickle, ONNX, XML, `.min.js`, etc.) or any unknown extension → **skip**
- **Source code** → extension in `_SOURCE_CODE_EXTENSIONS` (`.py`, `.js`, `.ts`, `.go`, `.java`, `.sql`, `.tf`, `.graphql`, etc.) → **split with cap**

A real repository with ~25,000 estimated input tokens (chunks) and ~9,000 output tokens (templates) represents a typical medium-sized project.

---

## Database Models

### `jobs` table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer PK | Auto-increment job ID |
| `project_name` | String(255) | Human-readable project name |
| `repo_url` | String(2048) | Repository URL (with embedded PAT) |
| `source_type` | String(20) | `github` or `azure_devops` |
| `ai_provider` | String(20) | `abacus`, `azure_ai`, or `mock` |
| `status` | String(20) | `queued`, `running`, `completed`, `failed` |
| `zip_generated` | Boolean | Whether the ZIP was successfully created |
| `zip_path` | String(512) | Filesystem path to the generated ZIP |
| `error_message` | Text | Error message (truncated to 2000 chars) |
| `created_at` | DateTime | Job submission time |
| `completed_at` | DateTime | Pipeline completion time |

### `job_progress` table
Tracks per-stage progress (percent, message) for each of the **8 pipeline stages** (including `embedding`).

### `job_logs` table
Stores all log entries (info, warn, error, debug) from the pipeline run for UI display.

---

## REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/jobs` | Submit a new job (repo URL + PAT + provider) |
| `GET` | `/api/jobs/{id}` | Get full job status and metadata |
| `GET` | `/api/jobs/{id}/progress` | Real-time 8-stage progress with percentages |
| `GET` | `/api/jobs/{id}/download` | Stream the generated ZIP file |
| `POST` | `/api/jobs/{id}/retry` | Re-queue a failed job |
| `GET` | `/api/jobs/{id}/logs` | Get all log entries for a job |
| `GET` | `/api/queue` | List all jobs (queued, running, completed) |
| `GET` | `/api/health` | Check API server health status |
| `GET` | `/api/providers` | List available AI providers and their status |
| `GET` | `/docs` | Interactive Swagger UI |

### Example Job Submission
```json
POST /api/jobs
{
  "project_name": "My App",
  "repo_url": "https://github.com/my-org/my-repo",
  "source_type": "github",
  "ai_provider": "azure_ai",
  "pat_token": "github_pat_..."
}
```

---

## Generated Documentation

Each job produces 6 markdown documents inside the ZIP:

| File | Contents |
| :--- | :--- |
| `PRD.md` | Product Requirements: features, scope, user stories, acceptance criteria |
| `Architecture-Design.md` | System architecture: components, data flow, tech stack, Mermaid diagrams |
| `Database-Design.md` | Database tables, columns, relationships, ERD |
| `API-Specification.md` | All endpoints, request/response schemas, auth methods |
| `Deployment-Guide.md` | Docker, CI/CD, local development setup, environment variables |
| `Review-and-TODO.md` | Code quality, security findings, TODO items, technical debt |

Plus an `index.json` manifest file listing all documents.

---

## Frontend — 4-Step Wizard

The frontend is a single-page wizard with full bidirectional navigation:

| Step | Screen | Left Action | Right Action |
| :--- | :--- | :--- | :--- |
| **Step 1** | Project Name | — | `Next →` button |
| **Step 2** | Connect Repository | `← back` | `next →` |
| **Step 3** | Pipeline (Live) | `← back` | `next →` |
| **Step 4** | Results & Download | `← back` | — |

### Live Queue — Job Switching
On Step 3, the **Live Queue** side panel lists all active and recent jobs. Each job row shows:
- An animated pulsing dot for running jobs
- A `View` button to switch the entire pipeline monitor to that job's progress
- A `×` dismiss button to hide it from the panel (frontend-only, no DB change)
- The currently monitored job is highlighted with an `active-job` border and a `Viewing` tag

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Git (must be on system `PATH`)
- PostgreSQL (optional — SQLite is used automatically as fallback)

### 1. Clone the Repository
```bash
git clone <this-repo-url>
cd ai-documentation
```

### 2. Virtual Environment Setup

It is strongly recommended to use a **virtual environment** to isolate project dependencies.

#### Windows (PowerShell)
```powershell
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# (Alternative: Command Prompt)
.\venv\Scripts\activate.bat
```

#### macOS / Linux
```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

Your shell prompt will change to show `(venv)` when the environment is active.

> **Tip**: To deactivate the virtual environment at any time, simply run `deactivate`.

### 3. Install Dependencies

With the virtual environment **activated**, install all dependencies at once using the combined dev requirements file:

```bash
# Install all dependencies (backend + runner + dev tools)
pip install -r requirements-dev.txt
```

Or install them separately if you only need a specific component:

```bash
# Backend only
pip install -r backend/requirements.txt

# Runner only
pip install -r runner/requirements.txt
```

### 4. Configure Environment
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Edit `.env` with your values (see [Configuration Reference](#configuration-reference)).

---

## Configuration Reference

All settings come from the `.env` file:

```ini
# ── Database ──────────────────────────────────────────────────────
DATABASE_URL=postgresql://aidocs:password@localhost:5432/aidocs
DATABASE_FALLBACK_URL=sqlite:///./data/aidocs.db

# ── Abacus AI (Claude Sonnet) ────────────────────────────────────
ABACUS_API_KEY=your-abacus-api-key-here
ABACUS_DEPLOYMENT_TOKEN=your-deployment-token-here
ABACUS_MODEL=claude-sonnet

# ── Azure AI Foundry (chat completions) ─────────────────────────
AZURE_AI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_AI_API_KEY=your-azure-api-key-here
AZURE_AI_DEPLOYMENT_NAME=gpt-4o       # or gpt-5.4, etc.
# AZURE_AI_API_VERSION=2024-06-01     # optional override

# ── Azure OpenAI Embeddings (RAG — Stage 3.5) ───────────────────
# Reuses AZURE_AI_API_KEY. Leave blank to disable RAG gracefully.
AZURE_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/openai/v1
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# ── Default Provider ─────────────────────────────────────────────
# Options: abacus | azure_ai | mock
DEFAULT_AI_PROVIDER=azure_ai

# ── Runner ───────────────────────────────────────────────────────
RUNNER_POLL_INTERVAL=2               # seconds between queue polls
MAX_JOB_DURATION_MINUTES=30

# ── Chunking / file handling ──────────────────────────────────────
# Max tokens to include from a single >3 MB source-code file.
# Subchunks beyond this cap are dropped (with a [WARN] log).
LARGE_SOURCE_FILE_MAX_TOKENS=40000

# ── Paths ────────────────────────────────────────────────────────
OUTPUT_DIR=./outputs
TEMP_DIR=./tmp

# ── Server ───────────────────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
```

> **Tip**: Leave Abacus keys as placeholders to skip it — the system detects placeholder strings and moves on to Azure AI. Leave `AZURE_EMBEDDING_ENDPOINT` blank to disable RAG — the pipeline continues without it.

---

## Running the Platform

### Option A: Standard (2-terminal setup)

**Terminal 1 — FastAPI Backend:**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Runner Daemon:**
```bash
python -m runner.main
```

**Open in Browser:**  
Navigate to `http://localhost:8000` — the frontend is served directly by FastAPI.

> **Note**: `backend/main.py` also launches the runner in a background thread automatically when using `uvicorn`, so in simple setups you only need one terminal.

### Option B: Open Frontend File Directly
```
Open frontend/ai-docs-generator.html in any modern browser
(while backend is running on port 8000)
```

---

## Docker Deployment

```bash
docker-compose up --build
```

The `docker-compose.yml` defines three services:
- **`api`** — FastAPI backend (port 8000)
- **`runner`** — Background pipeline daemon
- **`db`** — PostgreSQL 16 database (port 5432)

Templates are mounted as a read-only volume into the runner container.

---

## Running Tests

The test suite covers three scenarios:

1. **FallbackProvider Cascade** — Verifies Abacus → Azure → Mock fallback logic
2. **Clone with Absolute Paths** — Verifies path correctness and directory cleanup  
3. **Full Pipeline** — End-to-end StageManager test from clone to ZIP

```bash
python run_tests.py
```

Expected output:
```text
============================================================
Running Custom Test Suite...
============================================================
[1/3] Testing FallbackProvider sequence... => SUCCESS!
[2/3] Testing clone_repository with absolute paths... => SUCCESS!
[3/3] Testing StageManager pipeline end-to-end... => SUCCESS!
============================================================
ALL TESTS PASSED SUCCESSFULLY!
============================================================
```

---

## Troubleshooting

| Problem | Cause | Fix |
| :--- | :--- | :--- |
| `WinError 5 Access denied` on `.git/pack/*.idx` | Windows marks git pack files read-only | Fixed: `safe_rmtree()` unlocks and deletes recursively |
| Job always runs in Mock mode | Azure/Abacus key is placeholder or `max_tokens` rejected | Check `.env` keys; `is_available()` rejects placeholder strings; Azure uses `max_completion_tokens` automatically |
| `Clone completed but repository not found` | Relative path double-nesting in subprocess cwd | Fixed: all paths are resolved with `os.path.abspath()` before use |
| Frontend shows 304 Not Modified | Browser caching CSS/JS | Fixed: `Cache-Control: no-cache` headers added for all static files |
| PostgreSQL connection refused | DB not running | SQLite fallback activates automatically from `DATABASE_FALLBACK_URL` |
| Large source file produces too many chunks | Single file >3 MB exceeds cap | Increase `LARGE_SOURCE_FILE_MAX_TOKENS` in `.env` (default: 40,000) |
| Token Usage panel doesn't appear | Job hasn't reached chunking stage yet | Panel auto-reveals once `chunking` stage completes |
| Stage 3.5 shows "Skipped" in logs | `AZURE_EMBEDDING_*` not configured or API failed | Set `AZURE_EMBEDDING_ENDPOINT` + `AZURE_EMBEDDING_DEPLOYMENT` in `.env`; pipeline continues without RAG |
| `[RAG]` lines not appearing in Stage 6 output | Embeddings skipped or vector store not built | Check Stage 3.5 log for the error; confirm API key is valid |
| Embedding API returns 401 | Wrong or missing `AZURE_AI_API_KEY` | The embedding client reuses `AZURE_AI_API_KEY` — ensure it has access to the embedding deployment |

---

## License

MIT
