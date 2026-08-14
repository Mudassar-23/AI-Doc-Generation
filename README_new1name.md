# 🚀 Processing 8,000 Files & Pipeline Workflow Guide (`README_new1name.md`)

This guide provides a comprehensive breakdown answering repository scalability for 8,000+ files, exact execution time estimates, necessary configuration changes, and a complete stage-by-stage workflow explanation of the AI Documentation Generation Platform.

---

## 📑 Table of Contents
1. [Question 1: Can this platform handle a repository with 8,000 files?](#1-can-it-handle-8000-files)
2. [Question 2: How long does it take to process 8,000 files?](#2-how-much-time-does-it-take)
3. [Question 3: Recommended Configuration Changes for 8,000 Files](#3-recommended-configuration-changes)
4. [Question 4: Complete Stage-by-Stage Pipeline Workflow](#4-complete-stage-by-stage-pipeline-workflow)

---

## 1. Can it handle 8,000 files?

**YES, absolutely.** The platform is architected to handle large repositories with 8,000+ files efficiently without context window overflows or memory crashes.

### Why & How it Handles 8,000 Files:
1. **Intelligent File Filtering (Stage 2):**
   - Out of 8,000 total repository files, **30% to 70%** (typically 2,500 – 5,000 files) are automatically skipped via `.gitignore` and standard ignore filters (`DEFAULT_IGNORES`).
   - Skipped files include dependencies (`node_modules/`, `venv/`, `vendor/`), build outputs (`dist/`, `build/`, `target/`), lockfiles (`package-lock.json`, `yarn.lock`), binaries, images, fonts, minified assets, and compiled files.
2. **Three-Tier File Size Strategy:**
   - **≤ 700 KB:** Analyzed normally.
   - **700 KB – 3 MB:** Chunked internally into 4,000–5,000 token subchunks.
   - **> 3 MB Data/Generated Files (`.json`, `.csv`, `.parquet`, `.min.js`):** Automatically skipped.
   - **> 3 MB Source Code Files (`.py`, `.ts`, `.java`, `.go`, `.sql`):** Split internally and capped at `LARGE_SOURCE_FILE_MAX_TOKENS` (default: 40,000 tokens).
3. **Semantic Chunking (Stage 3):**
   - The remaining ~3,000–4,000 source code files are packed into semantic chunks targeting ~4,000 tokens (~16 KB of code) per chunk.
   - An 8,000-file repository typically produces approximately **800 to 1,200 semantic chunks**.
4. **Low Memory Footprint:**
   - The Python process streams file reads and metadata, keeping RAM usage low (~200–500 MB).

---

## 2. How much time does it take?

Processing an 8,000-file repository (~1,000 semantic chunks) takes approximately **25 to 45 minutes** when using a live AI provider (Azure AI Foundry / Abacus AI), or **~8 to 10 minutes** using the Mock Provider.

### Detailed Stage-by-Stage Time Estimate (8,000 Files ~ 1,000 Chunks):

| Stage | Action | Estimated Duration |
| :--- | :--- | :--- |
| **Stage 1** | Git Shallow Clone (`--depth 1`) | **15 – 45 seconds** |
| **Stage 2** | Discovery, `.gitignore` & Filtering (8,000 files) | **3 – 8 seconds** |
| **Stage 3** | Semantic Chunking & Token Packing | **3 – 10 seconds** |
| **Stage 3.5** | Azure OpenAI Vector Embeddings (RAG) | **20 – 35 seconds** |
| **Stage 4** | **LLM Chunk Analysis (1,000 API Calls)** | **22 – 38 minutes** *(~1.3–2.0s per chunk)* |
| **Stage 5** | Consolidate Structured Context JSON | **3 – 5 seconds** |
| **Stage 6** | Fill 6 Documentation Templates | **45 – 90 seconds** |
| **Stage 7** | Package Markdown Bundle into ZIP | **2 – 3 seconds** |
| **TOTAL** | **Full Pipeline Run Time** | ⏱️ **~25 to 45 Minutes** |

> ⚠️ **Note on API Rate Limits:** Total duration depends primarily on your LLM API Tier's **RPM (Requests Per Minute)** and **TPM (Tokens Per Minute)**. If rate limited, automatic exponential backoff retries will extend execution time.

---

## 3. Recommended Configuration Changes

To process large repositories (8,000+ files) without timing out or exceeding rate limits, update your `.env` configuration file with these settings:

### Required `.env` Overrides for 8,000 Files:

```ini
# 1. INCREASE MAXIMUM JOB DURATION
# Default is 30 minutes. Increase to 90 minutes to prevent job timeout during Stage 4.
MAX_JOB_DURATION_MINUTES=90

# 2. INCREASE TARGET CHUNK TOKENS (OPTIONAL SPEEDUP)
# Increasing TARGET_CHUNK_TOKENS from 4000 to 6000 packs more files per LLM call,
# reducing total LLM calls from ~1,000 down to ~650 (speeding up Stage 4 by ~35%).
TARGET_CHUNK_TOKENS=6000
MAX_CHUNK_TOKENS=7000

# 3. LARGE SOURCE FILE TOKEN CAP
# Keeps single massive code files (>3 MB) capped at 50,000 tokens max.
LARGE_SOURCE_FILE_MAX_TOKENS=50000

# 4. RUNNER QUEUE POLL INTERVAL
RUNNER_POLL_INTERVAL=2
```

---

## 4. Complete Stage-by-Stage Pipeline Workflow

Here is the exact step-by-step workflow of how data and execution flow through our **8-Stage Automated Pipeline**:

```
[User Request / API Post]
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 1: CLONE REPOSITORY (s1_clone.py)                         ║
║ • Performs shallow git clone (`git clone --depth 1`)            ║
║ • Injects PAT credentials securely for private repositories     ║
║ • Resolves absolute paths & handles Windows file locks          ║
╚═════════════════════════════════════════════════════════════════╝
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 2: ANALYZE CODEBASE (s2_analyze.py)                       ║
║ • Scans directory tree & parses .gitignore + DEFAULT_IGNORES     ║
║ • Filters out binaries, media, archives, node_modules, lockfiles║
║ • Categorizes code: Models, Controllers, Services, Config, etc.  ║
║ • Applies 3-tier size strategy (skip data >3MB, cap code >3MB)   ║
╚═════════════════════════════════════════════════════════════════╝
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 3: SEMANTIC CHUNKING (s3_chunk.py)                        ║
║ • Groups analyzed files by category in priority order          ║
║ • Packs files into semantic chunks targeting ~4,000-6,000 tokens║
║ • Computes token statistics per chunk                           ║
╚═════════════════════════════════════════════════════════════════╝
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 3.5: VECTOR EMBEDDINGS - RAG (embeddings.py)              ║
║ • Computes 1536-dim embeddings via Azure OpenAI Embeddings API  ║
║ • Builds in-memory ChunkVectorStore using cosine similarity     ║
║ • Gracefully skips if Azure Embeddings are not configured       ║
╚═════════════════════════════════════════════════════════════════╝
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 4: AI LLM CHUNK ANALYSIS (s4_llm_analyze.py)             ║
║ • Iterates sequentially through all generated chunks            ║
║ • Prompts LLM to extract structured JSON metadata per chunk     ║
║ • Extracts Tech Stack, Tables, Endpoints, Auth, Config, Security║
║ • Tracks real-time percentage progress in database & UI        ║
╚═════════════════════════════════════════════════════════════════╝
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 5: STRUCTURED CONTEXT BUILDING (s5_context_build.py)      ║
║ • Merges all chunk analysis JSONs into single Master Context   ║
║ • Deduplicates tech stack, database tables, and API routes      ║
║ • Maintains complete file path traceability for every fact      ║
╚═════════════════════════════════════════════════════════════════╝
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 6: RAG-ENHANCED TEMPLATE FILLING (s6_template_fill.py)    ║
║ • Loads 6 Markdown templates (PRD, Architecture, DB, API, etc.) ║
║ • RAG Search: Retrieves top-8 semantically relevant raw code    ║
║   snippets from ChunkVectorStore for each template query        ║
║ • Calls LLM to populate template placeholders with source facts ║
╚═════════════════════════════════════════════════════════════════╝
        │
        ▼
╔═════════════════════════════════════════════════════════════════╗
║ STAGE 7: PACKAGING & CLEANUP (s7_package.py)                    ║
║ • Writes generated markdown files to temporary directory        ║
║ • Creates `index.json` manifest with file metadata              ║
║ • Compresses files into `<project-name>-docs-job<id>.zip`       ║
║ • Cleans up cloned repo directory (`safe_rmtree`)               ║
║ • Marks Job as `completed` in DB with downloadable ZIP link     ║
╚═════════════════════════════════════════════════════════════════╝
```

---

### Step-by-Step Workflow Detail:

1. **Job Queueing & Dispatch:**
   - User submits project name, repository URL, source type, and PAT token via the REST API (`POST /api/jobs`) or Frontend UI.
   - The job is assigned a unique ID and inserted into the `jobs` database table with status `queued`.
   - `runner/main.py` runs a 2-second polling loop, picks up the FIFO queued job, and passes it to `StageManager`.

2. **Stage 1 — Clone Repository (`s1_clone.py`):**
   - The runner creates an isolated target directory `./tmp/job_{id}/repo`.
   - Executes `git clone --depth 1 <repo_url> <repo_dir>` via subprocess.
   - Shallow clone (`--depth 1`) fetches only the latest commit, minimizing clone time and bandwidth.
   - Injects PAT authentication securely without leaking credentials in logs.
   - Uses `safe_rmtree()` to handle Windows read-only `.git/objects/pack` file lock issues cleanly.

3. **Stage 2 — Codebase Discovery & Filtering (`s2_analyze.py`):**
   - Walks the repository directory structure via `discover_files()`.
   - Parses `.gitignore` and evaluates paths against `DEFAULT_IGNORES` (skipping `node_modules`, `vendor`, `.git`, lockfiles, build outputs, compiled binaries, images, and minified JS).
   - Categorizes each valid code file into one of 9 functional groups: *Documentation, Configuration, Models/Database, Services/Business Logic, Controllers/Routes, CI/CD & Docker, Tests, Utilities, General*.
   - Evaluates file size: normal (≤700 KB), chunk internally (700 KB – 3 MB), skip data (>3 MB), or split code with cap (>3 MB).

4. **Stage 3 — Semantic Chunking (`s3_chunk.py`):**
   - Groups analyzed files by category sorted by priority (Configuration first, Utilities last).
   - Packs files into semantic chunks targeting ~4,000 tokens (~16 KB text) per chunk, up to 5,000 tokens max.
   - Files exceeding single chunk bounds are cleanly sub-chunked by line boundary.
   - Computes estimated token counts for each chunk.

5. **Stage 3.5 — Compute Vector Embeddings / RAG Index (`embeddings.py` & `vector_store.py`):**
   - Optional RAG pipeline stage.
   - `AzureEmbedder` calls Azure OpenAI Embeddings API (`text-embedding-ada-002`) in batches of 16 chunks.
   - Each chunk receives a 1536-dimensional float vector embedding.
   - `ChunkVectorStore` builds an in-memory cosine-similarity vector store for semantic code search in Stage 6.
   - If embedding API is unconfigured or unavailable, logs gracefully and skips RAG without interrupting the pipeline.

6. **Stage 4 — AI LLM Chunk Analysis (`s4_llm_analyze.py`):**
   - Sequentially passes each semantic chunk to the AI provider (`Abacus AI` → `Azure AI Foundry` → `Mock Provider`).
   - Uses `CHUNK_ANALYSIS_SYSTEM_PROMPT` to extract structured JSON containing:
     - Project summary & purpose
     - Tech stack & dependencies
     - Architecture notes & design patterns
     - Database tables, columns & relations
     - API endpoints, HTTP methods & payloads
     - Authentication & Security mechanisms
     - Configuration environment variables
     - Source file path mappings
   - Updates progress percentage in `job_progress` table after every processed chunk.

7. **Stage 5 — Build Structured Context (`s5_context_build.py`):**
   - Aggregates all JSON analysis outputs from Stage 4 into a unified `Structured Context` object.
   - Deduplicates tech stack items, database schema definitions, API endpoints, and configuration settings.
   - Preserves complete source file traceability for all extracted knowledge.

8. **Stage 6 — RAG-Enhanced Template Filling (`s6_template_fill.py`):**
   - Loads 6 standard Markdown templates:
     1. `PRD.md` (Product Requirements Document)
     2. `Architecture-Design.md` (Architecture & System Design)
     3. `Database-Design.md` (Database Models & ERD)
     4. `API-Specification.md` (REST API Endpoints & Auth)
     5. `Deployment-Guide.md` (Docker & CI/CD Setup)
     6. `Review-and-TODO.md` (Security Audit & Technical Debt)
   - Extracts corresponding sections from `Structured Context`.
   - **RAG Retrieval:** If vector store is active, embeds a per-template query (e.g., `"system architecture components services modules layers data flow"` for Architecture Design) and retrieves top-8 raw code snippets, appending them to the LLM prompt as primary source evidence.
   - Prompts the LLM to fill template placeholders with precise, source-traced markdown content.

9. **Stage 7 — Package ZIP (`s7_package.py`):**
   - Saves all 6 filled Markdown documents to disk.
   - Generates `index.json` manifest with document list, file sizes, creation timestamps, and repository details.
   - Archives files into `./outputs/<project-name>-docs-job<id>.zip`.
   - Removes temporary cloned repository directory via `cleanup_temp()`.
   - Updates `jobs` table status to `completed`, sets `zip_generated = True`, and stores the download path `zip_path`.

---
