"""
Stage 2: Analyze Repository — discover, filter, and categorize all files.
"""
from typing import List
from runner.analysis.file_filter import discover_files
from runner.analysis.file_categorizer import categorize_file, detect_language


def analyze_repository(repo_path: str) -> dict:
    """
    Analyze a cloned repository — discover files, apply filters, categorize.

    Returns:
        {
            "all_files": [...],
            "analyzed_files": [...],
            "skipped_files": [...],
            "summary": { "total": int, "analyzed": int, "skipped": int }
        }
    """
    # Discover and filter files
    all_files = discover_files(repo_path)

    # Categorize analyzed files
    analyzed = []
    skipped = []

    for file_info in all_files:
        if file_info["status"] == "analyzed":
            file_info["category"] = categorize_file(file_info["path"])
            file_info["language"] = detect_language(file_info["path"])
            analyzed.append(file_info)
        else:
            skipped.append(file_info)

    return {
        "all_files": all_files,
        "analyzed_files": analyzed,
        "skipped_files": skipped,
        "summary": {
            "total": len(all_files),
            "analyzed": len(analyzed),
            "skipped": len(skipped),
        },
    }
