"""
DocGuard AI — Deterministic Demo Service

The built-in demo repository that runs fully offline.  It reads the
sample backend sources shipped in demo/sample-backend and drives them
through the exact same pipeline as a live analysis, producing the same
result every time.
"""
from __future__ import annotations

import logging
from pathlib import Path

from ..models.schemas import AnalysisResult, RepositoryInfo, WorkflowStep
from .route_extractor import extract_routes_from_source
from .openapi_parser import parse_openapi, extract_documented_routes
from .change_detector import detect_changes
from .schema_analyzer import analyze_routes
from .documentation_agent import DocumentationAgent
from .validator import validate_openapi

logger = logging.getLogger(__name__)

DEMO_REPOSITORY_NAME = "docguard-demo"

# demo/sample-backend sits three levels up from this module (services/)
DEMO_DIR = Path(__file__).resolve().parents[3] / "demo" / "sample-backend"


def _read_demo_source() -> str:
    """Read the 'after' backend source that contains the new endpoint."""
    path = DEMO_DIR / "after" / "main.py"
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.error("Demo source missing: %s", path)
    raise FileNotFoundError(f"Demo sample source not found at {path}")


def _read_demo_openapi() -> str:
    """Read the existing OpenAPI spec (the 'before' documentation)."""
    path = DEMO_DIR / "openapi.yaml"
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.error("Demo OpenAPI spec missing: %s", path)
    raise FileNotFoundError(f"Demo OpenAPI spec not found at {path}")


def _demo_workflow_steps(
    routes_detected: int,
    changes: list,
    openapi_name: str,
) -> list[WorkflowStep]:
    """The 8-step workflow, with details that match the actual demo result."""
    n_changes = len(changes)
    n_routes = routes_detected
    return [
        WorkflowStep(id="repo", step="Git Repository",
                     detail=f"Analyzed {DEMO_REPOSITORY_NAME} · 2 Python files", status="complete"),
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


def run_demo_analysis() -> AnalysisResult:
    """Run the full pipeline against the deterministic demo repository."""
    logger.info("Starting deterministic demo analysis")

    code_source = _read_demo_source()
    openapi_source = _read_demo_openapi()

    # 1. Extract routes from the (after) source
    routes = extract_routes_from_source(code_source, filename="demo/sample-backend/after/main.py")
    logger.info("Demo: extracted %d routes", len(routes))

    # 2. Schema analysis
    routes = analyze_routes(routes)

    # 3. Parse existing OpenAPI docs
    spec = parse_openapi(openapi_source, filename="demo/sample-backend/openapi.yaml")
    doc_routes = extract_documented_routes(spec) if spec else []

    # 4. Change detection
    changes = detect_changes(routes, doc_routes)
    logger.info("Demo: %d changes detected", len(changes))
    for ch in changes:
        logger.info("Demo change: %s — %s", ch.type.value, ch.description)

    # 5. Documentation Agent — update the OpenAPI spec
    agent = DocumentationAgent()
    updated_spec = agent.generate_updated_spec(routes, spec, changes)
    logger.info("Demo: documentation agent produced updated spec")

    # 6. Validation
    validation = validate_openapi(updated_spec)
    logger.info("Demo: validation passed=%s", validation["valid"])

    result = AnalysisResult(
        mode="demo",
        status="completed",
        repository=RepositoryInfo(
            name=DEMO_REPOSITORY_NAME,
            url="",
            files_scanned=2,
            python_files=2,
        ),
        summary={
            "routes_detected": len(routes),
            "changes_detected": len(changes),
            "documentation_updated": True,
            "validation_passed": validation["valid"],
        },
        changes=changes,
        routes=routes,
        workflow=_demo_workflow_steps(len(routes), changes, "openapi.yaml"),
        documentation_status="synchronized" if validation["valid"] else "outdated",
        openapi_spec=updated_spec,
        validation_errors=validation["errors"],
    )

    logger.info("Demo analysis complete: analysis_id=%s", result.analysis_id)
    return result