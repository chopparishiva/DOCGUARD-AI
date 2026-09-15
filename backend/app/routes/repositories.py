"""
DocGuard AI — Repository Routes
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import AnalysisResult, AnalyzeRequest
from ..services.analysis_runner import RepositoryError, run_live_analysis
from ..services.demo_service import run_demo_analysis
from ..storage import save

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_repository(payload: AnalyzeRequest) -> AnalysisResult:
    """
    Analyse a repository and return the full analysis result.

    When demo_mode is true the deterministic built-in demo repository is
    used and no network access is required.
    """
    logger.info("Analysis request received: demo_mode=%s repo=%s",
                payload.demo_mode, payload.repository_url)

    if payload.demo_mode:
        logger.info("Running deterministic demo analysis (offline)")
        result = run_demo_analysis()
        save(result)
        return result

    # Live mode: validate the URL first.
    if not payload.repository_url:
        raise HTTPException(status_code=400, detail="repository_url is required")

    try:
        result = await run_live_analysis(payload.repository_url)
    except RepositoryError as exc:
        logger.error("Repository analysis failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    save(result)
    return result