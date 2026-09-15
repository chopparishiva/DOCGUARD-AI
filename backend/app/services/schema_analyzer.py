"""
DocGuard AI — Schema Analyzer

Enriches detected routes with deeper type information by inspecting
Python type annotations, Pydantic model references, and return types.
Operates on the list of DetectedRoute objects produced by route_extractor.
"""
from __future__ import annotations

import ast
import logging
from typing import Optional

from ..models.schemas import DetectedRoute, RouteParameter

logger = logging.getLogger(__name__)

# Broader Python → OpenAPI type mapping
_PYTHON_TO_OPENAPI: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "List": "array",
    "dict": "object",
    "Dict": "object",
    "Optional": "string",
    "None": "string",
    "bytes": "string",
    "UUID": "string",
    "datetime": "string",
    "date": "string",
}

# Types that are already in OpenAPI form and must not be re-mapped.
_OPENAPI_TYPES = {"string", "integer", "number", "boolean", "array", "object"}


def _resolve_type_name(node: Optional[ast.expr]) -> str:
    """Best-effort extraction of a type name from an AST annotation node."""
    if node is None:
        return "string"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _resolve_type_name(node.value)
    return "string"


def _map_type(raw: str) -> str:
    if raw in _OPENAPI_TYPES:
        return raw
    return _PYTHON_TO_OPENAPI.get(raw, "string")


def analyze_routes(routes: list[DetectedRoute], source_map: dict[str, str] | None = None) -> list[DetectedRoute]:
    """
    Enrich each DetectedRoute with better type info.

    Parameters
    ----------
    routes : list[DetectedRoute]
        Routes extracted by route_extractor.
    source_map : dict[str, str] | None
        Optional {filename: source_code} for deeper AST inspection.
    """
    # If source_map is provided, we could do deeper analysis.
    # For the MVP we mostly rely on what route_extractor already got.
    # This pass normalises types and ensures consistency.

    for route in routes:
        for param in route.parameters:
            param.type = _map_type(param.type)
        if route.return_type:
            route.return_type = _map_type(route.return_type)

    logger.info("Schema analysis complete for %d routes", len(routes))
    return routes
