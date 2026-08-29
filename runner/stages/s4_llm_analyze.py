"""
Stage 4: LLM Chunk Analysis — send each chunk to the AI provider for structured knowledge extraction.
Parallel processing via ThreadPoolExecutor for significantly faster throughput.
"""
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from runner.prompts import (
    CHUNK_ANALYSIS_SYSTEM_PROMPT,
    build_chunk_analysis_prompt,
)
from runner.analysis.chunk_builder import format_chunk_for_prompt
from runner.providers.base import BaseProvider
from runner.config import RunnerConfig


def analyze_chunks_with_llm(
    provider: BaseProvider,
    chunks: List[dict],
    project_name: str,
    repo_url: str,
    progress_callback=None,
) -> List[dict]:
    """
    Send each chunk to the LLM for structured knowledge extraction.
    Processes chunks in parallel using ThreadPoolExecutor for faster throughput.

    Args:
        provider: The AI provider to use.
        chunks: List of chunk dicts from the chunk builder.
        project_name: Project name for context.
        repo_url: Repository URL for context.
        progress_callback: Optional callback(chunk_number, total_chunks, message).

    Returns:
        List of parsed analysis dicts (one per chunk), ordered by original chunk index.
    """
    total = len(chunks)
    max_workers = RunnerConfig.LLM_PARALLEL_WORKERS

    # Thread-safe counter for progress reporting
    completed_count = 0
    progress_lock = threading.Lock()

    def analyze_one(index: int, chunk: dict) -> tuple[int, dict]:
        """Analyze a single chunk and return (original_index, analysis_dict)."""
        nonlocal completed_count
        chunk_num = index + 1

        chunk_content = format_chunk_for_prompt(chunk)
        user_prompt = build_chunk_analysis_prompt(
            project_name=project_name,
            repo_url=repo_url,
            chunk_number=chunk_num,
            total_chunks=total,
            chunk_category=chunk["category"],
            file_list=chunk["file_paths"],
            chunk_content=chunk_content,
        )

        # Retry loop with exponential backoff for 429 rate-limit errors
        max_retries = RunnerConfig.MAX_LLM_RETRIES
        delay = RunnerConfig.RETRY_BASE_DELAY
        last_exc = None
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = provider.analyze_chunk(
                    system_prompt=CHUNK_ANALYSIS_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                )
                break  # success
            except Exception as exc:
                last_exc = exc
                exc_str = str(exc)
                # Retry on rate-limit (429) or transient errors
                if attempt < max_retries and ("429" in exc_str or "rate" in exc_str.lower() or "timeout" in exc_str.lower() or "connection" in exc_str.lower()):
                    wait = delay * (2 ** attempt)
                    print(f"[Stage 4] Chunk {chunk_num} hit rate limit/timeout (attempt {attempt+1}/{max_retries+1}). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    break

        if response is None:
            print(f"[Stage 4] [WARN] Chunk {chunk_num} failed after retries ({last_exc}). Continuing with fallback.")
            analysis = {
                "project_summary": f"Chunk {chunk_num} ({chunk['category']}) analyzed with basic heuristics.",
                "tech_stack": [],
                "architecture_notes": "",
                "database_tables": [],
                "api_endpoints": [],
                "authentication": {"type": "Unknown", "source": "fallback"},
                "configuration": {"env_vars": [], "source": ["fallback"]},
                "business_logic": "",
                "dependencies": {"runtime": [], "dev": [], "source": "fallback"},
                "source_files": chunk.get("file_paths", []),
                "_fallback": True,
            }
        else:
            analysis = _parse_analysis_response(response)

        analysis["_chunk_number"] = chunk_num
        analysis["_chunk_category"] = chunk["category"]
        analysis["_chunk_files"] = chunk["file_paths"]

        # Thread-safe progress update
        with progress_lock:
            nonlocal completed_count
            completed_count += 1
            done = completed_count
        if progress_callback:
            progress_callback(
                done, total,
                f"Analyzing chunk {chunk_num}/{total}: {chunk['category']}"
            )

        return index, analysis

    # Submit all chunks to the thread pool
    print(f"[Stage 4] Starting parallel LLM analysis — {total} chunks, {max_workers} workers")
    results: list[Optional[dict]] = [None] * total

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(analyze_one, i, chunk): i
            for i, chunk in enumerate(chunks)
        }
        for future in as_completed(futures):
            try:
                idx, analysis = future.result()
                results[idx] = analysis
            except Exception as e:
                print(f"[Stage 4] [WARN] Unexpected error in worker: {e}")

    # Fill any missing indices with basic fallback
    for idx in range(total):
        if results[idx] is None:
            results[idx] = {
                "project_summary": f"Chunk {idx+1} analysis fallback.",
                "tech_stack": [],
                "architecture_notes": "",
                "database_tables": [],
                "api_endpoints": [],
                "authentication": {"type": "Unknown", "source": "fallback"},
                "configuration": {"env_vars": [], "source": ["fallback"]},
                "business_logic": "",
                "dependencies": {"runtime": [], "dev": [], "source": "fallback"},
                "source_files": chunks[idx].get("file_paths", []),
                "_chunk_number": idx + 1,
                "_chunk_category": chunks[idx].get("category", "General"),
                "_chunk_files": chunks[idx].get("file_paths", []),
            }

    print(f"[Stage 4] Parallel analysis complete — {total} chunks processed")
    return results


def _parse_analysis_response(response: str) -> dict:
    """Parse LLM response as JSON, with fallback handling."""
    # Try direct JSON parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    import re
    json_match = re.search(r'```(?:json)?\s*\n(.*?)```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Fallback — return raw text as a single-field dict
    return {
        "project_summary": response[:500],
        "tech_stack": [],
        "architecture_notes": "",
        "database_tables": [],
        "api_endpoints": [],
        "authentication": {"type": "Unknown", "source": "parse_error"},
        "configuration": {"env_vars": [], "source": ["parse_error"]},
        "business_logic": "",
        "dependencies": {"runtime": [], "dev": [], "source": "parse_error"},
        "source_files": [],
        "_parse_error": "Could not parse LLM response as JSON",
    }
