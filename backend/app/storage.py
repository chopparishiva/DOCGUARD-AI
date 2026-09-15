"""
DocGuard AI — In-memory analysis store.

A tiny module-level registry so the various routes can share analysis
results.  This is an MVP convenience — no database, no persistence.
"""
from __future__ import annotations

import threading
from typing import Optional

from .models.schemas import AnalysisResult

_lock = threading.Lock()
_analyses: dict[str, AnalysisResult] = {}


def save(result: AnalysisResult) -> None:
    with _lock:
        _analyses[result.analysis_id] = result


def get(analysis_id: str) -> Optional[AnalysisResult]:
    with _lock:
        return _analyses.get(analysis_id)


def clear() -> None:
    with _lock:
        _analyses.clear()