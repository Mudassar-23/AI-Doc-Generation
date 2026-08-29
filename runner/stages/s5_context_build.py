"""
Stage 5: Build Structured Context — consolidate all chunk analyses.
"""
from typing import List
from runner.analysis.context_builder import consolidate_chunk_analyses


def build_structured_context(chunk_analyses: List[dict]) -> dict:
    """
    Consolidate chunk analyses into a single Structured Context.

    Args:
        chunk_analyses: List of analysis dicts from Stage 4.

    Returns:
        Consolidated Structured Context dict.
    """
    return consolidate_chunk_analyses(chunk_analyses)
