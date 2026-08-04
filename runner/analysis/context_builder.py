"""
Context builder — consolidates chunk analyses into a single Structured Context.

Responsibilities:
  - Merge duplicate information across chunks
  - Resolve conflicts
  - Preserve source traceability
  - Build the final context document that feeds template filling
"""
import json
from typing import List, Dict, Any


def merge_lists(existing: list, new: list) -> list:
    """Merge two lists, removing duplicates."""
    combined = list(existing)
    for item in new:
        if isinstance(item, dict):
            # For dicts, check if a matching entry already exists
            if item not in combined:
                combined.append(item)
        elif item not in combined:
            combined.append(item)
    return combined


def merge_strings(existing: str, new: str) -> str:
    """Merge two strings, combining non-empty values."""
    if not existing or existing.startswith("[Mock"):
        return new
    if not new or new.startswith("[Mock"):
        return existing
    if existing == new:
        return existing
    return f"{existing}\n{new}"


def consolidate_chunk_analyses(analyses: List[dict]) -> dict:
    """
    Consolidate multiple chunk analyses into a single Structured Context.

    Args:
        analyses: List of chunk analysis dicts (from LLM responses).

    Returns:
        Consolidated Structured Context dict.
    """
    context = {
        "SYSTEM_OVERVIEW": {
            "description": "",
            "project_type": "",
            "sources": [],
        },
        "TECH_STACK": {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "other_tools": [],
            "sources": [],
        },
        "ARCHITECTURE": {
            "pattern": "",
            "components": [],
            "data_flow": "",
            "sources": [],
        },
        "DATABASE": {
            "engine": "",
            "tables": [],
            "relationships": "",
            "sources": [],
        },
        "API_ENDPOINTS": {
            "endpoints": [],
            "authentication": "",
            "sources": [],
        },
        "AUTHENTICATION": {
            "type": "",
            "details": "",
            "sources": [],
        },
        "CONFIGURATION": {
            "env_vars": [],
            "config_files": [],
            "sources": [],
        },
        "ENV_VARIABLES": {
            "variables": [],
            "sources": [],
        },
        "MODULES": {
            "modules": [],
            "sources": [],
        },
        "SERVICES": {
            "services": [],
            "sources": [],
        },
        "DEPENDENCIES": {
            "runtime": [],
            "dev": [],
            "sources": [],
        },
        "DEPLOYMENT": {
            "method": "",
            "details": "",
            "sources": [],
        },
        "DOCKER": {
            "has_dockerfile": False,
            "has_compose": False,
            "services": [],
            "sources": [],
        },
        "CI_CD": {
            "platform": "",
            "workflows": [],
            "sources": [],
        },
        "CODING_PATTERNS": {
            "patterns": [],
            "conventions": "",
            "sources": [],
        },
        "SECURITY": {
            "observations": "",
            "concerns": "",
            "sources": [],
        },
        "BUSINESS_LOGIC": {
            "rules": "",
            "sources": [],
        },
        "MISSING_FEATURES": {
            "items": [],
            "sources": [],
        },
        "ASSUMPTIONS": {
            "items": [],
            "sources": [],
        },
        "UNKNOWN_AREAS": {
            "items": [],
            "sources": [],
        },
    }

    for analysis in analyses:
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except json.JSONDecodeError:
                continue

        if not isinstance(analysis, dict):
            continue

        # Merge tech stack
        tech_stack = analysis.get("tech_stack", [])
        if isinstance(tech_stack, list):
            context["TECH_STACK"]["languages"] = merge_lists(
                context["TECH_STACK"]["languages"], tech_stack
            )

        # Merge architecture
        arch_notes = analysis.get("architecture_notes", "")
        if arch_notes:
            context["ARCHITECTURE"]["pattern"] = merge_strings(
                context["ARCHITECTURE"]["pattern"], arch_notes
            )

        # Merge database tables
        tables = analysis.get("database_tables", [])
        if isinstance(tables, list):
            context["DATABASE"]["tables"] = merge_lists(
                context["DATABASE"]["tables"], tables
            )

        # Merge API endpoints
        endpoints = analysis.get("api_endpoints", [])
        if isinstance(endpoints, list):
            context["API_ENDPOINTS"]["endpoints"] = merge_lists(
                context["API_ENDPOINTS"]["endpoints"], endpoints
            )

        # Merge authentication
        auth = analysis.get("authentication", {})
        if isinstance(auth, dict) and auth.get("type") and auth["type"] != "Unknown":
            context["AUTHENTICATION"]["type"] = auth.get("type", "")
            context["AUTHENTICATION"]["details"] = merge_strings(
                context["AUTHENTICATION"]["details"],
                auth.get("details", "")
            )
            if auth.get("source"):
                context["AUTHENTICATION"]["sources"].append(auth["source"])

        # Merge configuration
        config = analysis.get("configuration", {})
        if isinstance(config, dict):
            env_vars = config.get("env_vars", [])
            if isinstance(env_vars, list):
                context["CONFIGURATION"]["env_vars"] = merge_lists(
                    context["CONFIGURATION"]["env_vars"], env_vars
                )
                # Also populate ENV_VARIABLES section
                for var in env_vars:
                    if var and not any(v.get("name") == var for v in context["ENV_VARIABLES"]["variables"]):
                        context["ENV_VARIABLES"]["variables"].append({
                            "name": var,
                            "purpose": "Detected in configuration",
                            "required": True,
                        })

        # Merge dependencies
        deps = analysis.get("dependencies", {})
        if isinstance(deps, dict):
            runtime = deps.get("runtime", [])
            dev = deps.get("dev", [])
            if isinstance(runtime, list):
                context["DEPENDENCIES"]["runtime"] = merge_lists(
                    context["DEPENDENCIES"]["runtime"], runtime
                )
            if isinstance(dev, list):
                context["DEPENDENCIES"]["dev"] = merge_lists(
                    context["DEPENDENCIES"]["dev"], dev
                )

        # Merge string fields
        context["SYSTEM_OVERVIEW"]["description"] = merge_strings(
            context["SYSTEM_OVERVIEW"]["description"],
            analysis.get("project_summary", "")
        )
        context["DEPLOYMENT"]["details"] = merge_strings(
            context["DEPLOYMENT"]["details"],
            analysis.get("deployment_notes", "")
        )
        context["DOCKER"]["sources"].extend(
            [f for f in [analysis.get("docker_notes", "")] if f and f != "[Mock] Docker configuration not found in this chunk."]
        )
        context["SECURITY"]["observations"] = merge_strings(
            context["SECURITY"]["observations"],
            analysis.get("security_notes", "")
        )
        context["BUSINESS_LOGIC"]["rules"] = merge_strings(
            context["BUSINESS_LOGIC"]["rules"],
            analysis.get("business_logic", "")
        )
        context["CODING_PATTERNS"]["conventions"] = merge_strings(
            context["CODING_PATTERNS"]["conventions"],
            analysis.get("coding_patterns", "")
        )

        # Merge source files
        source_files = analysis.get("source_files", [])
        if isinstance(source_files, list):
            context["SYSTEM_OVERVIEW"]["sources"] = merge_lists(
                context["SYSTEM_OVERVIEW"]["sources"], source_files
            )

        # Merge missing features
        missing = analysis.get("missing_features", "")
        if missing and not missing.startswith("[Mock"):
            context["MISSING_FEATURES"]["items"].append(missing)

        # Merge assumptions
        assumptions = analysis.get("assumptions", "")
        if assumptions and not assumptions.startswith("[Mock"):
            context["ASSUMPTIONS"]["items"].append(assumptions)

        # Merge unknown areas
        unknown = analysis.get("unknown_areas", "")
        if unknown and not unknown.startswith("[Mock"):
            context["UNKNOWN_AREAS"]["items"].append(unknown)

    return context
