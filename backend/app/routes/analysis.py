"""
DocGuard AI — Analysis Routes
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import AnalysisResult
from ..storage import get

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str) -> AnalysisResult:
    """Return the status and detected API changes for an analysis."""
    result = get(analysis_id)
    if result is None:
        logger.warning("Analysis not found: %s", analysis_id)
        raise HTTPException(status_code=404, detail="Analysis not found")
    logger.info("Analysis retrieved: %s (status=%s)", analysis_id, result.status.value)
    return result