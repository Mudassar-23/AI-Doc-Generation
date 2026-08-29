"""
Stage 6: Template Filling — load templates, map context, call LLM to fill.
Optionally enhanced with RAG: if a ChunkVectorStore is provided, each template
retrieves its top-K most semantically relevant raw code chunks and appends them
to the prompt for higher-fidelity generation.
"""
import os
import json
from typing import List, Dict, Optional
from runner.config import RunnerConfig
from runner.prompts import (
    TEMPLATE_FILLING_SYSTEM_PROMPT,
    build_template_fill_prompt,
    get_relevant_context_sections,
    TEMPLATE_SEMANTIC_QUERIES,
)
from runner.providers.base import BaseProvider


# Template files in generation order (6 templates)
TEMPLATE_FILES = [
    "PRD.md",
    "Architecture Design.md",
    "Database Design.md",
    "API Specification.md",
    "Deployment Guide.md",
    "Review and TODO.md",
]

# Output filenames (slightly different from template names)
OUTPUT_FILENAMES = {
    "PRD.md": "PRD.md",
    "Architecture Design.md": "Architecture-Design.md",
    "Database Design.md": "Database-Design.md",
    "API Specification.md": "API-Specification.md",
    "Deployment Guide.md": "Deployment-Guide.md",
    "Review and TODO.md": "Review-and-TODO.md",
}


from runner.analysis.chunk_builder import estimate_tokens

# Max chars of raw chunk content to inject per retrieved chunk
_RAG_CONTENT_CHARS = 600
# Number of top-K chunks to retrieve per template
_RAG_TOP_K = 8


def _build_rag_section(retrieved_chunks: list) -> str:
    """
    Format retrieved chunks as a markdown section to append to the template prompt.
    Only includes file paths and a short content preview.
    """
    if not retrieved_chunks:
        return ""

    lines = ["\n\n## Relevant Code Snippets (retrieved by semantic search)\n"]
    lines.append("The following raw code fragments are the most relevant sections of the "
                 "repository for this document. Use them as primary evidence.\n")

    for i, chunk in enumerate(retrieved_chunks, 1):
        paths = ", ".join(chunk.get("file_paths", []))
        category = chunk.get("category", "")
        content = chunk.get("content", "")[:_RAG_CONTENT_CHARS]
        lines.append(f"### Snippet {i} — [{category}] {paths}\n```\n{content}\n```\n")

    return "\n".join(lines)


import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


def fill_templates(
    provider: BaseProvider,
    structured_context: dict,
    project_name: str,
    repo_url: str,
    progress_callback=None,
    vector_store=None,     # Optional[ChunkVectorStore] — from Stage 3.5
    embedder=None,         # Optional[AzureEmbedder]   — from Stage 3.5
) -> Dict[str, str]:
    """
    Fill all documentation templates in parallel using the Structured Context.

    Args:
        provider: AI provider for template filling.
        structured_context: Consolidated context from Stage 5.
        project_name: Project name.
        repo_url: Repository URL.
        progress_callback: Optional callback(template_num, total, message).
        vector_store: Optional ChunkVectorStore for RAG retrieval.
        embedder: Optional AzureEmbedder used to embed the per-template query.

    Returns:
        Tuple of (Dict[output_filename -> generated_content], total_in_tokens, total_out_tokens).
    """
    templates_dir = RunnerConfig.TEMPLATES_DIR
    documents = {}
    total = len(TEMPLATE_FILES)

    rag_active = (
        vector_store is not None
        and embedder is not None
        and vector_store.is_built()
        and embedder.is_available()
    )

    print("\n" + "=" * 60)
    print("         DOCUMENT GENERATION & TOKEN STATISTICS")
    if rag_active:
        print("         [RAG ACTIVE — semantic chunk retrieval enabled]")
    print(f"         [Parallel Generation: {total} documents concurrently]")
    print("=" * 60)

    completed_count = 0
    progress_lock = threading.Lock()

    def generate_single_template(index: int, template_name: str):
        nonlocal completed_count
        template_num = index + 1
        output_name = OUTPUT_FILENAMES.get(template_name, template_name)

        try:
            # Load template
            template_path = os.path.join(templates_dir, template_name)
            if not os.path.exists(template_path):
                return index, output_name, f"# {output_name}\n\nTemplate not found: {template_name}", 0, 0

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Get relevant context sections for this template
            relevant_context = get_relevant_context_sections(template_name, structured_context)
            context_json = json.dumps(relevant_context, indent=2, default=str)

            # RAG: retrieve top-K semantically relevant raw chunks for this template
            rag_section = ""
            if rag_active:
                query = TEMPLATE_SEMANTIC_QUERIES.get(template_name, template_name)
                retrieved = vector_store.search_by_text_embedding(embedder, query, top_k=_RAG_TOP_K)
                rag_section = _build_rag_section(retrieved)
                if retrieved:
                    print(f"  [RAG] {output_name}: {len(retrieved)} chunks retrieved")

            # Build prompt (append RAG snippets after structured context)
            user_prompt = build_template_fill_prompt(
                project_name=project_name,
                repo_url=repo_url,
                template_content=template_content,
                structured_context=context_json + rag_section,
            )

            # Estimate input tokens (Prompt + System Prompt)
            in_tokens = estimate_tokens(user_prompt) + estimate_tokens(TEMPLATE_FILLING_SYSTEM_PROMPT)

            # Call LLM
            response = provider.fill_template(
                system_prompt=TEMPLATE_FILLING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            # Estimate output tokens (Response)
            out_tokens = estimate_tokens(response) if response else 0
            content = response if response else f"# {output_name}\n\nGeneration failed."

            with progress_lock:
                completed_count += 1
                done = completed_count
                print(f"[{done}/{total}] Completed: {output_name:<25} | Input: {in_tokens:<5} | Output: {out_tokens:<5}")

            if progress_callback:
                progress_callback(
                    done, total,
                    f"Generated {output_name} ({done}/{total})"
                )

            return index, output_name, content, in_tokens, out_tokens

        except Exception as e:
            print(f"[Stage 6] [WARN] Error generating {output_name}: {e}")
            fallback_content = f"# {output_name}\n\n*Document generation encountered an error: {e}*\n"
            with progress_lock:
                completed_count += 1
                done = completed_count
            if progress_callback:
                progress_callback(
                    done, total,
                    f"Processed {output_name} ({done}/{total})"
                )
            return index, output_name, fallback_content, 0, 0

    # Run template generations with balanced concurrency (3 workers to prevent 429 burst rate limits)
    max_workers = min(3, total)
    results = [None] * total
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, tpl in enumerate(TEMPLATE_FILES):
            futures[executor.submit(generate_single_template, i, tpl)] = i
            import time
            time.sleep(0.3)  # Small stagger to prevent simultaneous token burst

        for future in as_completed(futures):
            idx, out_name, content, in_tok, out_tok = future.result()
            results[idx] = (out_name, content, in_tok, out_tok)

    total_in_tokens = 0
    total_out_tokens = 0
    for out_name, content, in_tok, out_tok in results:
        documents[out_name] = content
        total_in_tokens += in_tok
        total_out_tokens += out_tok

    print("-" * 60)
    print(f"Total Templates: {total:<12} | Total Input: {total_in_tokens:<5} | Total Output: {total_out_tokens:<5}")
    print("=" * 60 + "\n")

    return documents, total_in_tokens, total_out_tokens
