"""
Stage 6: Template Filling — load templates, map context, call LLM to fill.
"""
import os
import json
from typing import List, Dict
from runner.config import RunnerConfig
from runner.prompts import (
    TEMPLATE_FILLING_SYSTEM_PROMPT,
    build_template_fill_prompt,
    get_relevant_context_sections,
    TEMPLATE_CONTEXT_MAP,
)
from runner.providers.base import BaseProvider


# Template files in generation order
TEMPLATE_FILES = [
    "PRD.md",
    "Architecture Design.md",
    "Database Design.md",
    "API Specification.md",
    "Deployment Guide.md",
    "Run Locally.md",
    "Stack and Techniques.md",
    "Review and TODO.md",
]

# Output filenames (slightly different from template names)
OUTPUT_FILENAMES = {
    "PRD.md": "PRD.md",
    "Architecture Design.md": "Architecture-Design.md",
    "Database Design.md": "Database-Design.md",
    "API Specification.md": "API-Specification.md",
    "Deployment Guide.md": "Deployment-Guide.md",
    "Run Locally.md": "Run-Locally.md",
    "Stack and Techniques.md": "Stack-and-Techniques.md",
    "Review and TODO.md": "Review-and-TODO.md",
}


from runner.analysis.chunk_builder import estimate_tokens


def fill_templates(
    provider: BaseProvider,
    structured_context: dict,
    project_name: str,
    repo_url: str,
    progress_callback=None,
) -> Dict[str, str]:
    """
    Fill all documentation templates using the Structured Context.

    Args:
        provider: AI provider for template filling.
        structured_context: Consolidated context from Stage 5.
        project_name: Project name.
        repo_url: Repository URL.
        progress_callback: Optional callback(template_num, total, message).

    Returns:
        Dict of output_filename -> generated content.
    """
    templates_dir = RunnerConfig.TEMPLATES_DIR
    documents = {}
    total = len(TEMPLATE_FILES)

    print("\n" + "=" * 60)
    print("         DOCUMENT GENERATION & TOKEN STATISTICS")
    print("=" * 60)
    
    total_in_tokens = 0
    total_out_tokens = 0

    for i, template_name in enumerate(TEMPLATE_FILES):
        template_num = i + 1
        output_name = OUTPUT_FILENAMES.get(template_name, template_name)

        if progress_callback:
            progress_callback(
                template_num, total,
                f"Generating {output_name} ({template_num}/{total})"
            )

        # Load template
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            documents[output_name] = f"# {output_name}\n\nTemplate not found: {template_name}"
            continue

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Get relevant context sections for this template
        relevant_context = get_relevant_context_sections(template_name, structured_context)
        context_json = json.dumps(relevant_context, indent=2, default=str)

        # Build prompt
        user_prompt = build_template_fill_prompt(
            project_name=project_name,
            repo_url=repo_url,
            template_content=template_content,
            structured_context=context_json,
        )

        # Estimate input tokens (Prompt + System Prompt)
        in_tokens = estimate_tokens(user_prompt) + estimate_tokens(TEMPLATE_FILLING_SYSTEM_PROMPT)
        total_in_tokens += in_tokens

        # Call LLM
        response = provider.fill_template(
            system_prompt=TEMPLATE_FILLING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Estimate output tokens (Response)
        out_tokens = estimate_tokens(response) if response else 0
        total_out_tokens += out_tokens

        print(f"Document: {output_name:<25} | Input Tokens: {in_tokens:<5} | Output Tokens: {out_tokens:<5}")

        # Store the generated document
        documents[output_name] = response if response else f"# {output_name}\n\nGeneration failed."

    print("-" * 60)
    print(f"Total Templates: {total:<12} | Total Input: {total_in_tokens:<5} | Total Output: {total_out_tokens:<5}")
    print("=" * 60 + "\n")

    return documents, total_in_tokens, total_out_tokens
