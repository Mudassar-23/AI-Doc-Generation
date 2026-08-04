"""
Stage 3: Build Chunks — group analyzed files into semantic chunks.
"""
from typing import List
from runner.analysis.chunk_builder import build_chunks


def build_file_chunks(repo_path: str, analyzed_files: List[dict]) -> List[dict]:
    """
    Build semantic chunks from analyzed files and print token estimation statistics.

    Args:
        repo_path: Path to the cloned repository.
        analyzed_files: List of analyzed file dicts with category info.

    Returns:
        List of chunk dicts ready for LLM analysis.
    """
    chunks = build_chunks(repo_path, analyzed_files)

    print("\n" + "=" * 60)
    print("           SEMANTIC CHUNKING & TOKEN ESTIMATION")
    print("=" * 60)
    total_tokens = 0
    for chunk in chunks:
        print(f"Chunk #{chunk['chunk_number']} | Category: {chunk['category']} | Estimated Tokens: {chunk['estimated_tokens']} | Lines: {chunk['line_count']}")
        for path in chunk['file_paths']:
            print(f"  - {path}")
        total_tokens += chunk['estimated_tokens']
    print("-" * 60)
    print(f"Total Chunks: {len(chunks)} | Total Estimated Tokens: {total_tokens}")
    print("=" * 60 + "\n")

    return chunks
