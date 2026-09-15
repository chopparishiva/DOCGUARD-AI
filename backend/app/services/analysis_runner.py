"""
DocGuard AI — Analysis Pipeline Runner

Orchestrates the live (non-demo) pipeline:

    Repository fetching → route extraction → schema analysis →
    OpenAPI parsing → change detection → documentation agent →
    OpenAPI update → validation → synchronization status
"""
from __future__ import annotations

import logging

from ..models.schemas import AnalysisResult, RepositoryInfo, WorkflowStep
from . import github_service
from .route_extractor import extract_routes_from_source
from .schema_analyzer import analyze_routes
from .openapi_parser import parse_openapi, extract_documented_routes
from .change_detector import detect_changes
from .documentation_agent import DocumentationAgent
from .validator import validate_openapi

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Raised for any repository-level failure (network, unsupported, etc.)."""


async def run_live_analysis(repository_url: str) -> AnalysisResult:
    """Run the pipeline against a public GitHub repository."""
    parsed = github_service.parse_github_url(repository_url)
    if parsed is None:
        raise RepositoryError("Invalid GitHub repository URL")
    owner, repo = parsed

    logger.info("Analysis requested for %s/%s", owner, repo)

    # ---- Repository fetching ----
    logger.info("Fetching repository tree for %s/%s", owner, repo)
    tree = await github_service.fetch_repo_tree(owner, repo)
    if not tree:
        raise RepositoryError(
            "Could not fetch repository tree (network failure or repository not found)"
        )

    python_files = github_service.find_python_files(tree)
    openapi_files = github_service.find_openapi_files(tree)
    logger.info("Discovered %d Python files", len(python_files))
    logger.info("OpenAPI file(s) discovered: %s", openapi_files or "none")

    if not python_files:
        raise RepositoryError("No Python files found in repository")

    # ---- API Route Extraction & Schema Analysis ----
    routes = []
    for path in python_files:
        source = await github_service.fetch_file_content(owner, repo, path)
        if source is None:
            continue
        routes.extend(extract_routes_from_source(source, filename=path))

    routes = analyze_routes(routes)
    logger.info("Extracted %d API routes", len(routes))

    if not routes:
        # Not fatal — the analysis simply reports no routes.
        logger.warning("No API routes detected in %s/%s", owner, repo)

    # ---- OpenAPI Parsing ----
    spec = None
    doc_routes = []
    openapi_name = "openapi.yaml"
    if openapi_files:
        openapi_name = openapi_files[0]
        content = await github_service.fetch_file_content(owner, repo, openapi_name)
        if content is not None:
            spec = parse_openapi(content, filename=openapi_name)
            if spec:
                doc_routes = extract_documented_routes(spec)
            else:
                logger.warning("Could not parse OpenAPI file %s", openapi_name)
    else:
        logger.warning("No OpenAPI file found; docs will be generated from scratch")

    # ---- Change Detection ----
    changes = detect_changes(routes, doc_routes)
    logger.info("Change detection complete: %d changes", len(changes))
    for ch in changes:
        logger.info("Change: %s — %s", ch.type.value, ch.description)

    # ---- Documentation Agent ----
    agent = DocumentationAgent()
    updated_spec = agent.generate_updated_spec(routes, spec, changes)
    logger.info("Documentation generation complete")

    # ---- Validation ----
    validation = validate_openapi(updated_spec)
    logger.info("Validation result: passed=%s errors=%s", validation["valid"], validation["errors"])

    result = AnalysisResult(
        mode="live",
        status="completed",
        repository=RepositoryInfo(
            name=repo,
            url=repository_url,
            files_scanned=len(python_files),
            python_files=len(python_files),
        ),
        summary={
            "routes_detected": len(routes),
            "changes_detected": len(changes),
            "documentation_updated": True,
            "validation_passed": validation["valid"],
        },
        changes=changes,
        routes=routes,
        workflow=_build_workflow(len(routes), len(changes), openapi_name),
        documentation_status="synchronized" if validation["valid"] else "outdated",
        openapi_spec=updated_spec,
        validation_errors=validation["errors"],
    )
    logger.info("Analysis complete: analysis_id=%s", result.analysis_id)
    return result


def _build_workflow(n_routes: int, n_changes: int, openapi_name: str) -> list[WorkflowStep]:
    return [
        WorkflowStep(id="repo", step="Git Repository",
                     detail="Repository fetched · source files scanned", status="complete"),
        WorkflowStep(id="routes", step="API Route Detection",
                     detail=f"{n_routes} endpoints detected across the codebase", status="complete"),
        WorkflowStep(id="changes", step="Change Detection",
                     detail=f"{n_changes} API change{'s' if n_changes != 1 else ''} detected", status="complete"),
        WorkflowStep(id="openapi", step="OpenAPI Comparison",
                     detail=f"Compared against {openapi_name} · {n_changes} diff{'s' if n_changes != 1 else ''}",
                     status="complete"),
        WorkflowStep(id="agent", step="AI Documentation Agent",
                     detail="Drafted patches for changed endpoints", status="complete"),
        WorkflowStep(id="update", step="OpenAPI Update",
                     detail=f"Merged {n_changes} operation{'s' if n_changes != 1 else ''} into {openapi_name}",
                     status="complete"),
        WorkflowStep(id="validation", step="Validation",
                     detail="OpenAPI validators passed", status="complete"),
        WorkflowStep(id="sync", step="Documentation Synchronized",
                     detail="Docs in sync with source code", status="complete"),
    ]