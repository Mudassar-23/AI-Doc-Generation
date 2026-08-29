"""
Chunk builder — groups analyzed files into semantic chunks for LLM processing.

Chunking strategy:
  1. Group files by category
  2. Pack files into chunks targeting ~4000 tokens each (maximum ~5000 tokens)
  3. Order chunks by priority (Config → Models → Services → Controllers → ...)
  4. Large files (>700 KB or >5000 tokens) are chunked internally
  5. Files exceeding 8000 tokens are processed in full without truncation (token usage printed)
"""
import os
from typing import List, Dict
from runner.config import RunnerConfig


# Category priority order (lower = higher priority, sent to LLM first)
CATEGORY_PRIORITY = {
    "Documentation": 1,
    "Configuration": 2,
    "Models / Database": 3,
    "Services / Business Logic": 4,
    "Controllers / Routes": 5,
    "CI/CD & Docker": 6,
    "Tests": 7,
    "Utilities / Helpers": 8,
    "General": 9,
}


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (1 token ≈ 4 chars)."""
    return len(text) // RunnerConfig.TOKEN_CHAR_RATIO


def read_file_content(full_path: str, max_tokens: int = None, display_path: str = None) -> str:
    """
    Read file content without truncation.
    If estimated tokens exceed max_tokens (default 8000), print token count.
    """
    if max_tokens is None:
        max_tokens = RunnerConfig.MAX_FILE_TOKENS

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return "[ERROR: Could not read file]"

    tokens = estimate_tokens(content)
    if tokens > max_tokens:
        path_str = display_path or full_path
        print(f"[INFO] File '{path_str}' exceeds {max_tokens} tokens ({tokens} tokens used). Processing without truncation.")

    return content


def split_file_into_subchunks(
    file_path: str,
    content: str,
    target_tokens: int = RunnerConfig.TARGET_CHUNK_TOKENS,
    max_tokens: int = RunnerConfig.MAX_CHUNK_TOKENS,
) -> List[dict]:
    """
    Chunk a large file internally into multiple sub-parts based on lines or character slices.
    Target ~4000 tokens, maximum ~5000 tokens per sub-part.
    """
    lines = content.splitlines(keepends=True)
    max_chars = target_tokens * RunnerConfig.TOKEN_CHAR_RATIO

    # If single line or no lines split, slice by characters directly
    if len(lines) <= 1 and len(content) > max_chars:
        subchunks = []
        part = 1
        for i in range(0, len(content), max_chars):
            sub_text = content[i : i + max_chars]
            tokens = estimate_tokens(sub_text)
            subchunks.append({
                "path": f"{file_path} (part {part})",
                "content": sub_text,
                "tokens": tokens,
                "lines": sub_text.count("\n") + 1,
            })
            part += 1
        return subchunks

    subchunks = []
    current_lines = []
    current_tokens = 0
    part = 1

    for line in lines:
        line_tokens = estimate_tokens(line)

        # If a single line itself exceeds target_tokens, flush current and slice the line
        if line_tokens > target_tokens:
            if current_lines:
                sub_text = "".join(current_lines)
                subchunks.append({
                    "path": f"{file_path} (part {part})",
                    "content": sub_text,
                    "tokens": current_tokens,
                    "lines": len(current_lines),
                })
                part += 1
                current_lines = []
                current_tokens = 0

            for i in range(0, len(line), max_chars):
                sub_text = line[i : i + max_chars]
                tokens = estimate_tokens(sub_text)
                subchunks.append({
                    "path": f"{file_path} (part {part})",
                    "content": sub_text,
                    "tokens": tokens,
                    "lines": sub_text.count("\n") + 1,
                })
                part += 1
            continue

        if current_lines and (current_tokens + line_tokens > target_tokens):
            sub_text = "".join(current_lines)
            subchunks.append({
                "path": f"{file_path} (part {part})",
                "content": sub_text,
                "tokens": current_tokens,
                "lines": len(current_lines),
            })
            part += 1
            current_lines = [line]
            current_tokens = line_tokens
        else:
            current_lines.append(line)
            current_tokens += line_tokens

    if current_lines:
        sub_text = "".join(current_lines)
        path_label = f"{file_path} (part {part})" if part > 1 else file_path
        subchunks.append({
            "path": path_label,
            "content": sub_text,
            "tokens": current_tokens,
            "lines": len(current_lines),
        })

    return subchunks



def build_chunks(
    repo_path: str,
    analyzed_files: List[dict],
) -> List[dict]:
    """
    Build semantic chunks from analyzed files.

    Args:
        repo_path: Path to the cloned repository.
        analyzed_files: List of file dicts with 'path', 'category', 'size', optionally 'chunk_internally'.

    Returns:
        List of chunk dicts: {
            "chunk_number": int,
            "category": str,
            "files": [{"path": str, "content": str}],
            "file_paths": [str],
            "estimated_tokens": int,
            "line_count": int,
        }
    """
    target_tokens = RunnerConfig.TARGET_CHUNK_TOKENS
    max_chunk_tokens = RunnerConfig.MAX_CHUNK_TOKENS
    large_source_token_cap = RunnerConfig.LARGE_SOURCE_FILE_MAX_TOKENS

    # Group files by category
    categories: Dict[str, List[dict]] = {}
    for file_info in analyzed_files:
        cat = file_info.get("category", "General")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(file_info)

    # Sort categories by priority
    sorted_cats = sorted(
        categories.keys(),
        key=lambda c: CATEGORY_PRIORITY.get(c, 99)
    )

    chunks = []
    chunk_number = 1

    for category in sorted_cats:
        files = categories[category]
        current_chunk_files = []
        current_tokens = 0
        current_lines = 0

        for file_info in files:
            full_path = os.path.join(repo_path, file_info["path"])
            content = read_file_content(full_path, display_path=file_info["path"])
            file_tokens = estimate_tokens(content)

            # ----------------------------------------------------------------
            # Path A: large_source — >3 MB source code file
            #   Split into 4k-token subchunks and cap at LARGE_SOURCE_FILE_MAX_TOKENS
            # ----------------------------------------------------------------
            if file_info.get("large_source", False):
                # Flush whatever is already accumulating for this category
                if current_chunk_files:
                    chunks.append({
                        "chunk_number": chunk_number,
                        "category": category,
                        "files": current_chunk_files,
                        "file_paths": [f["path"] for f in current_chunk_files],
                        "estimated_tokens": current_tokens,
                        "line_count": current_lines,
                    })
                    chunk_number += 1
                    current_chunk_files = []
                    current_tokens = 0
                    current_lines = 0

                subchunks = split_file_into_subchunks(
                    file_info["path"], content,
                    target_tokens=target_tokens,
                    max_tokens=max_chunk_tokens,
                )

                # Apply token cap: include subchunks until the cap is reached
                included_tokens = 0
                included = []
                for sub in subchunks:
                    if included_tokens + sub["tokens"] > large_source_token_cap:
                        break
                    included.append(sub)
                    included_tokens += sub["tokens"]

                dropped = len(subchunks) - len(included)
                if dropped:
                    print(
                        f"[WARN] '{file_info['path']}' exceeds LARGE_SOURCE_FILE_MAX_TOKENS "
                        f"({large_source_token_cap:,}). "
                        f"Including {len(included)}/{len(subchunks)} subchunks "
                        f"({included_tokens:,} tokens). {dropped} subchunk(s) dropped."
                    )

                for sub in included:
                    chunks.append({
                        "chunk_number": chunk_number,
                        "category": category,
                        "files": [{"path": sub["path"], "content": sub["content"]}],
                        "file_paths": [sub["path"]],
                        "estimated_tokens": sub["tokens"],
                        "line_count": sub["lines"],
                    })
                    chunk_number += 1
                continue

            # ----------------------------------------------------------------
            # Path B: chunk_internally — 700 KB–3 MB file, or >5 000 tokens
            # ----------------------------------------------------------------
            should_chunk_internally = file_info.get("chunk_internally", False) or file_tokens > max_chunk_tokens

            if should_chunk_internally:
                # Flush existing chunk in progress for this category
                if current_chunk_files:
                    chunks.append({
                        "chunk_number": chunk_number,
                        "category": category,
                        "files": current_chunk_files,
                        "file_paths": [f["path"] for f in current_chunk_files],
                        "estimated_tokens": current_tokens,
                        "line_count": current_lines,
                    })
                    chunk_number += 1
                    current_chunk_files = []
                    current_tokens = 0
                    current_lines = 0

                # Internal chunking for large file (no token cap)
                subchunks = split_file_into_subchunks(
                    file_info["path"], content, target_tokens=target_tokens, max_tokens=max_chunk_tokens
                )
                for sub in subchunks:
                    chunks.append({
                        "chunk_number": chunk_number,
                        "category": category,
                        "files": [{"path": sub["path"], "content": sub["content"]}],
                        "file_paths": [sub["path"]],
                        "estimated_tokens": sub["tokens"],
                        "line_count": sub["lines"],
                    })
                    chunk_number += 1
                continue

            # Standard file packaging: flush current chunk if target_tokens exceeded
            file_lines = content.count("\n") + 1
            if current_chunk_files and (current_tokens + file_tokens) > target_tokens:
                chunks.append({
                    "chunk_number": chunk_number,
                    "category": category,
                    "files": current_chunk_files,
                    "file_paths": [f["path"] for f in current_chunk_files],
                    "estimated_tokens": current_tokens,
                    "line_count": current_lines,
                })
                chunk_number += 1
                current_chunk_files = []
                current_tokens = 0
                current_lines = 0

            # Add file to current chunk
            current_chunk_files.append({"path": file_info["path"], "content": content})
            current_tokens += file_tokens
            current_lines += file_lines

        # Flush remaining files in this category
        if current_chunk_files:
            chunks.append({
                "chunk_number": chunk_number,
                "category": category,
                "files": current_chunk_files,
                "file_paths": [f["path"] for f in current_chunk_files],
                "estimated_tokens": current_tokens,
                "line_count": current_lines,
            })
            chunk_number += 1

    return chunks


def format_chunk_for_prompt(chunk: dict) -> str:
    """Format a chunk's files into a single string for the LLM prompt."""
    parts = []
    for file_info in chunk["files"]:
        parts.append(f"--- FILE: {file_info['path']} ---")
        parts.append(file_info["content"])
        parts.append("")

    return "\n".join(parts)

