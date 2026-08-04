"""
Stage 4: LLM Chunk Analysis — send each chunk to the AI provider for structured knowledge extraction.
"""
import json
from typing import List
from runner.prompts import (
    CHUNK_ANALYSIS_SYSTEM_PROMPT,
    build_chunk_analysis_prompt,
)
from runner.analysis.chunk_builder import format_chunk_for_prompt
from runner.providers.base import BaseProvider


def analyze_chunks_with_llm(
    provider: BaseProvider,
    chunks: List[dict],
    project_name: str,
    repo_url: str,
    progress_callback=None,
) -> List[dict]:
    """
    Send each chunk to the LLM for structured knowledge extraction.

    Args:
        provider: The AI provider to use.
        chunks: List of chunk dicts from the chunk builder.
        project_name: Project name for context.
        repo_url: Repository URL for context.
        progress_callback: Optional callback(chunk_number, total_chunks, message).

    Returns:
        List of parsed analysis dicts (one per chunk).
    """
    analyses = []
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        chunk_num = i + 1

        if progress_callback:
            progress_callback(
                chunk_num, total,
                f"Analyzing chunk {chunk_num}/{total}: {chunk['category']}"
            )

        # Format chunk content for the prompt
        chunk_content = format_chunk_for_prompt(chunk)

        # Build the analysis prompt
        user_prompt = build_chunk_analysis_prompt(
            project_name=project_name,
            repo_url=repo_url,
            chunk_number=chunk_num,
            total_chunks=total,
            chunk_category=chunk["category"],
            file_list=chunk["file_paths"],
            chunk_content=chunk_content,
        )

        # Call the LLM
        response = provider.analyze_chunk(
            system_prompt=CHUNK_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Parse the JSON response
        analysis = _parse_analysis_response(response)
        analysis["_chunk_number"] = chunk_num
        analysis["_chunk_category"] = chunk["category"]
        analysis["_chunk_files"] = chunk["file_paths"]
        analyses.append(analysis)

    return analyses


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
