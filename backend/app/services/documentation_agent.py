"""
DocGuard AI — Documentation Agent

Deterministic rule-based documentation generation engine.
Takes detected code routes, existing OpenAPI spec, and detected changes,
then produces an updated OpenAPI document.

Architecture is designed so an LLM provider can be plugged in later
without changing the public interface.
"""
from __future__ import annotations

import copy
import logging
from typing import Any, Optional

from ..models.schemas import (
    ChangeType,
    DetectedChange,
    DetectedRoute,
    RouteParameter,
)

logger = logging.getLogger(__name__)


# ---------- Type mapping for generated schemas ----------

_PYTHON_TO_JSON_SCHEMA: dict[str, dict[str, str]] = {
    "string": {"type": "string"},
    "integer": {"type": "integer"},
    "number": {"type": "number"},
    "boolean": {"type": "boolean"},
    "array": {"type": "array", "items": {"type": "string"}},
    "object": {"type": "object"},
}


def _param_to_schema(param: RouteParameter) -> dict[str, Any]:
    return copy.deepcopy(_PYTHON_TO_JSON_SCHEMA.get(param.type, {"type": "string"}))


class DocumentationAgent:
    """
    Generates updated OpenAPI documentation from detected changes.

    In a future version this class can accept an LLM provider to produce
    richer descriptions and summaries.  The current rule-based engine is
    fully deterministic and works offline.
    """

    def __init__(self, llm_provider: Any | None = None):
        """
        Parameters
        ----------
        llm_provider : Any | None
            Reserved for future LLM integration.  When None (default),
            the agent uses deterministic rules only.
        """
        self.llm = llm_provider

    def generate_updated_spec(
        self,
        code_routes: list[DetectedRoute],
        existing_spec: dict[str, Any],
        changes: list[DetectedChange],
    ) -> dict[str, Any]:
        """
        Produce an updated OpenAPI spec.

        Steps:
        1. Deep-copy the existing spec (or create a skeleton).
        2. Apply each change.
        3. Ensure all code routes are present.
        """
        spec = copy.deepcopy(existing_spec) if existing_spec else self._empty_spec()

        # Ensure required top-level fields
        spec.setdefault("openapi", "3.0.3")
        spec.setdefault("info", {"title": "API Documentation", "version": "1.0.0"})
        spec.setdefault("paths", {})

        # Apply changes
        for change in changes:
            self._apply_change(spec, change, code_routes)

        # Upsert every code route so spec matches reality
        for route in code_routes:
            self._upsert_route(spec, route)

        logger.info(
            "Documentation agent: updated spec now has %d paths",
            len(spec.get("paths", {})),
        )
        return spec

    # ---------- Internal helpers ----------

    def _empty_spec(self) -> dict[str, Any]:
        return {
            "openapi": "3.0.3",
            "info": {"title": "API Documentation", "version": "1.0.0"},
            "paths": {},
        }

    def _apply_change(
        self,
        spec: dict[str, Any],
        change: DetectedChange,
        code_routes: list[DetectedRoute],
    ) -> None:
        paths = spec.setdefault("paths", {})

        if change.type == ChangeType.ADDED_ENDPOINT:
            # Find the matching code route to populate the spec
            after = change.after or {}
            method = (after.get("method") or "").lower()
            path = after.get("path", "")
            if method and path:
                matching = [r for r in code_routes if r.method.lower() == method and r.path == path]
                if matching:
                    self._upsert_route(spec, matching[0])

        elif change.type == ChangeType.REMOVED_ENDPOINT:
            before = change.before or {}
            method = (before.get("method") or "").lower()
            path = before.get("path", "")
            if path in paths and method in paths[path]:
                del paths[path][method]
                # Clean up empty path objects
                if not paths[path]:
                    del paths[path]

        elif change.type == ChangeType.PATH_CHANGED:
            # Remove old path entry, add new one
            before = change.before or {}
            after = change.after or {}
            old_method = (before.get("method") or "").lower()
            old_path = before.get("path", "")
            if old_path in paths and old_method in paths[old_path]:
                del paths[old_path][old_method]
                if not paths[old_path]:
                    del paths[old_path]
            # Add the new route
            new_method = (after.get("method") or "").lower()
            new_path = after.get("path", "")
            matching = [r for r in code_routes if r.method.lower() == new_method and r.path == new_path]
            if matching:
                self._upsert_route(spec, matching[0])

        elif change.type in (ChangeType.PARAMETER_ADDED, ChangeType.PARAMETER_REMOVED, ChangeType.PARAMETER_TYPE_CHANGED):
            # Rebuild the path entry from the code route
            after = change.after or {}
            before = change.before or {}
            method = (after.get("method") or before.get("method") or "").lower()
            path = after.get("path") or before.get("path") or ""
            matching = [r for r in code_routes if r.method.lower() == method and r.path == path]
            if matching:
                self._upsert_route(spec, matching[0])

    def _upsert_route(self, spec: dict[str, Any], route: DetectedRoute) -> None:
        """Insert or update a single route in the spec."""
        paths = spec.setdefault("paths", {})
        path_obj = paths.setdefault(route.path, {})

        parameters = []
        for p in route.parameters:
            param: dict[str, Any] = {
                "name": p.name,
                "in": p.location,
                "required": p.required,
                "schema": _param_to_schema(p),
            }
            parameters.append(param)

        operation: dict[str, Any] = {
            "summary": self._generate_summary(route),
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    },
                }
            },
        }
        if parameters:
            operation["parameters"] = parameters

        path_obj[route.method.lower()] = operation

    def _generate_summary(self, route: DetectedRoute) -> str:
        """Generate a simple human-readable summary for an endpoint."""
        verb = route.method.capitalize()
        path_display = route.path.replace("{", "<").replace("}", ">")
        if route.function_name:
            return f"{verb} {path_display} — {route.function_name}"
        return f"{verb} {path_display}"
