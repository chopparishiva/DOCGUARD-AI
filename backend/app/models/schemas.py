"""
DocGuard AI — Pydantic models for API request/response schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- Enums ----------

class ChangeType(str, Enum):
    ADDED_ENDPOINT = "ADDED_ENDPOINT"
    REMOVED_ENDPOINT = "REMOVED_ENDPOINT"
    PATH_CHANGED = "PATH_CHANGED"
    METHOD_CHANGED = "METHOD_CHANGED"
    PARAMETER_ADDED = "PARAMETER_ADDED"
    PARAMETER_REMOVED = "PARAMETER_REMOVED"
    PARAMETER_TYPE_CHANGED = "PARAMETER_TYPE_CHANGED"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------- Request Models ----------

class AnalyzeRequest(BaseModel):
    repository_url: str = Field(..., description="GitHub repository URL")
    demo_mode: bool = Field(default=False, description="Run in deterministic demo mode")


# ---------- Route / Parameter Models ----------

class RouteParameter(BaseModel):
    name: str
    type: str = "string"
    required: bool = True
    location: str = "path"  # path | query


class DetectedRoute(BaseModel):
    method: str
    path: str
    function_name: str = ""
    parameters: list[RouteParameter] = Field(default_factory=list)
    return_type: Optional[str] = None
    source_file: str = ""


class DocumentedRoute(BaseModel):
    method: str
    path: str
    parameters: list[RouteParameter] = Field(default_factory=list)
    summary: Optional[str] = None


# ---------- Change Detection ----------

class DetectedChange(BaseModel):
    type: ChangeType
    severity: Severity = Severity.WARNING
    description: str = ""
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None


# ---------- Workflow ----------

class WorkflowStep(BaseModel):
    id: str
    step: str
    detail: str
    status: str = "pending"  # pending | active | complete


# ---------- Analysis ----------

class RepositoryInfo(BaseModel):
    name: str
    url: str = ""
    files_scanned: int = 0
    python_files: int = 0


class AnalysisSummary(BaseModel):
    routes_detected: int = 0
    changes_detected: int = 0
    documentation_updated: bool = False
    validation_passed: bool = False


class AnalysisResult(BaseModel):
    analysis_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    mode: str = "live"
    status: AnalysisStatus = AnalysisStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    repository: RepositoryInfo = Field(default_factory=RepositoryInfo)
    summary: AnalysisSummary = Field(default_factory=AnalysisSummary)
    changes: list[DetectedChange] = Field(default_factory=list)
    routes: list[DetectedRoute] = Field(default_factory=list)
    workflow: list[WorkflowStep] = Field(default_factory=list)
    documentation_status: str = "pending"
    openapi_spec: Optional[dict[str, Any]] = None
    validation_errors: list[str] = Field(default_factory=list)


# ---------- Documentation ----------

class DocumentationResponse(BaseModel):
    analysis_id: str
    status: str
    openapi_spec: dict[str, Any]
    validation: dict[str, Any]
    changes_applied: int = 0


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "DocGuard AI"
