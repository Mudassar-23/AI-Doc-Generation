"""
Stage 7: Package — build index.json and ZIP all documents.
"""
import os
import json
import zipfile
from datetime import datetime
from typing import Dict
from runner.config import RunnerConfig


def package_documents(
    documents: Dict[str, str],
    project_name: str,
    repo_url: str,
    source_type: str,
    job_id: int,
) -> str:
    """
    Package all generated documents into a ZIP file.

    Args:
        documents: Dict of filename -> content.
        project_name: Project name.
        repo_url: Repository URL.
        source_type: "github" or "azure_devops".
        job_id: Job ID for unique output path.

    Returns:
        Path to the generated ZIP file.
    """
    # Build index.json manifest
    manifest = {
        "project": project_name,
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "source": {
            "type": source_type,
            "url": repo_url,
        },
        "files": [],
        "generator": "AI Docs Generator",
        "version": "1.0.0",
    }

    for filename, content in documents.items():
        word_count = len(content.split()) if content else 0
        manifest["files"].append({
            "name": filename,
            "words": word_count,
            "size_bytes": len(content.encode("utf-8")),
        })

    documents["index.json"] = json.dumps(manifest, indent=2)

    # Create output directory
    os.makedirs(RunnerConfig.OUTPUT_DIR, exist_ok=True)

    # Build ZIP
    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in project_name)
    zip_filename = f"{safe_name}-docs-job{job_id}.zip"
    zip_path = os.path.join(RunnerConfig.OUTPUT_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        folder_name = f"{safe_name}-docs"
        for filename, content in documents.items():
            zf.writestr(f"{folder_name}/{filename}", content)

    return zip_path
