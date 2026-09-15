"""
DocGuard AI — Documentation Routes
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import DocumentationResponse
from ..storage import get
from ..services.validator import validate_openapi

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documentation", tags=["documentation"])


@router.get("/{analysis_id}", response_model=DocumentationResponse)
async def get_documentation(analysis_id: str) -> DocumentationResponse:
    """Return the generated/updated OpenAPI documentation and validation result."""
    result = get(analysis_id)
    if result is None:
        logger.warning("Documentation requested for unknown analysis: %s", analysis_id)
        raise HTTPException(status_code=404, detail="Analysis not found")

    if result.openapi_spec is None:
        logger.warning("No OpenAPI spec generated for analysis: %s", analysis_id)
        raise HTTPException(status_code=400, detail="No OpenAPI documentation available")

    validation = validate_openapi(result.openapi_spec)
    logger.info("Documentation returned for %s (valid=%s)", analysis_id, validation["valid"])

    return DocumentationResponse(
        analysis_id=analysis_id,
        status=result.documentation_status,
        openapi_spec=result.openapi_spec,
        validation=validation,
        changes_applied=len(result.changes),
    )