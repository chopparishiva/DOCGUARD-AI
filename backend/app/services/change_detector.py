"""
DocGuard AI — Change Detector

Compares API routes detected in source code against routes documented
in an existing OpenAPI specification and produces a list of changes.

Detection order matters: path-signature changes (e.g. /users →
/users/{user_id}) are found FIRST so they surface as a single
PATH_CHANGED change instead of a confusing ADDED+REMOVED pair.
"""
from __future__ import annotations

import logging
import re

from ..models.schemas import (
    ChangeType,
    DetectedChange,
    DetectedRoute,
    DocumentedRoute,
    Severity,
)

logger = logging.getLogger(__name__)

_PATH_PARAM_RE = re.compile(r"\{[^}]+\}")


def _strip_params(path: str) -> str:
    """Remove path-parameter segments: /users/{id} → /users."""
    return _PATH_PARAM_RE.sub("", path).rstrip("/")


def detect_changes(
    code_routes: list[DetectedRoute],
    doc_routes: list[DocumentedRoute],
) -> list[DetectedChange]:
    """Compare code routes against documented routes and return structured changes."""
    changes: list[DetectedChange] = []

    # Index documented routes by (method, path)
    doc_index: dict[tuple[str, str], DocumentedRoute] = {
        (dr.method, dr.path): dr for dr in doc_routes
    }
    code_index: dict[tuple[str, str], DetectedRoute] = {
        (cr.method, cr.path): cr for cr in code_routes
    }

    # Tracks code/doc pairs that share an exact path (both sides matched).
    matched_code_keys: set[tuple[str, str]] = set()

    # ---- Phase 1: path-signature changes ----
    # A code route and a doc route with the same method whose paths match
    # after stripping path params, but differ exactly, is a PATH_CHANGED.
    unmatched_code = {k: cr for k, cr in code_index.items() if k not in doc_index}
    for key, cr in unmatched_code.items():
        base = _strip_params(cr.path)
        for dr in doc_routes:
            if dr.method != cr.method:
                continue
            if _strip_params(dr.path) != base:
                continue
            if dr.path == cr.path:
                continue
            changes.append(DetectedChange(
                type=ChangeType.PATH_CHANGED,
                severity=Severity.WARNING,
                description=f"Path signature changed: {dr.path} → {cr.path}",
                before={"method": dr.method, "path": dr.path},
                after={"method": cr.method, "path": cr.path},
            ))
            # Compare parameters across the signature change.
            _compare_params(cr, dr, changes)
            matched_code_keys.add(key)
            break

    # ---- Phase 2: added / removed endpoints for everything unmatched ----
    for key, cr in code_index.items():
        if key in matched_code_keys or key in doc_index:
            continue
        changes.append(DetectedChange(
            type=ChangeType.ADDED_ENDPOINT,
            severity=Severity.WARNING,
            description=f"New endpoint {cr.method} {cr.path} is not documented",
            after={"method": cr.method, "path": cr.path, "function": cr.function_name},
        ))

    # Doc routes consumed by a PATH_CHANGED detection share the same method
    # and a stripping-identical base path with one of the matched code routes.
    matched_bases = {
        cr.method + "|" + _strip_params(cr.path)
        for k in matched_code_keys
        for cr in [code_index[k]]
    }
    for key, dr in doc_index.items():
        if key in code_index:
            continue
        if dr.method + "|" + _strip_params(dr.path) in matched_bases:
            continue
        changes.append(DetectedChange(
            type=ChangeType.REMOVED_ENDPOINT,
            severity=Severity.WARNING,
            description=f"Documented endpoint {dr.method} {dr.path} no longer exists in code",
            before={"method": dr.method, "path": dr.path},
        ))

    # ---- Phase 3: exact-match routes — compare parameters ----
    for key in set(code_index.keys()) & set(doc_index.keys()):
        _compare_params(code_index[key], doc_index[key], changes)

    logger.info("Change detection complete: %d changes found", len(changes))
    return changes


def _compare_params(
    cr: DetectedRoute,
    dr: DocumentedRoute,
    changes: list[DetectedChange],
) -> None:
    """Compare parameters between a code route and a documented route."""
    code_params = {p.name: p for p in cr.parameters}
    doc_params = {p.name: p for p in dr.parameters}

    for name, cp in code_params.items():
        if name not in doc_params:
            changes.append(DetectedChange(
                type=ChangeType.PARAMETER_ADDED,
                severity=Severity.INFO,
                description=f"Parameter '{name}' added to {cr.method} {cr.path}",
                before={"method": cr.method, "path": cr.path},
                after={
                    "method": cr.method,
                    "path": cr.path,
                    "parameter": name,
                    "type": cp.type,
                    "required": cp.required,
                },
            ))
        elif cp.type != doc_params[name].type:
            changes.append(DetectedChange(
                type=ChangeType.PARAMETER_TYPE_CHANGED,
                severity=Severity.WARNING,
                description=f"Parameter '{name}' type changed on {cr.method} {cr.path}",
                before={
                    "method": cr.method,
                    "path": cr.path,
                    "parameter": name,
                    "type": doc_params[name].type,
                },
                after={
                    "method": cr.method,
                    "path": cr.path,
                    "parameter": name,
                    "type": cp.type,
                },
            ))

    for name in doc_params:
        if name not in code_params:
            changes.append(DetectedChange(
                type=ChangeType.PARAMETER_REMOVED,
                severity=Severity.WARNING,
                description=f"Parameter '{name}' removed from {cr.method} {cr.path}",
                before={
                    "method": cr.method,
                    "path": cr.path,
                    "parameter": name,
                    "type": doc_params[name].type,
                },
            ))