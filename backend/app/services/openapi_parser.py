"""
DocGuard AI — OpenAPI Parser

Parses existing OpenAPI specifications (JSON or YAML) and produces a
normalised list of DocumentedRoute objects for comparison with code.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import yaml

from ..models.schemas import DocumentedRoute, RouteParameter

logger = logging.getLogger(__name__)

_SUPPORTED_METHODS = {"get", "post", "put", "patch", "delete"}


def parse_openapi(content: str, filename: str = "") -> Optional[dict[str, Any]]:
    """Parse a raw OpenAPI spec string (JSON or YAML) into a dict. Returns None on failure."""
    # Try JSON first
    try:
        data = json.loads(content)
        logger.info("Parsed OpenAPI spec as JSON from %s", filename or "<string>")
        return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Try YAML
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            logger.info("Parsed OpenAPI spec as YAML from %s", filename or "<string>")
            return data
    except yaml.YAMLError as exc:
        logger.warning("YAML parse error in %s: %s", filename, exc)

    return None


def extract_documented_routes(spec: dict[str, Any]) -> list[DocumentedRoute]:
    """Extract normalised route info from an OpenAPI spec dict."""
    paths = spec.get("paths", {})
    routes: list[DocumentedRoute] = []

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in _SUPPORTED_METHODS:
            operation = path_item.get(method)
            if operation is None:
                continue

            params: list[RouteParameter] = []
            for p in operation.get("parameters", []):
                if not isinstance(p, dict):
                    continue
                params.append(RouteParameter(
                    name=p.get("name", ""),
                    type=_schema_type(p.get("schema", {})),
                    required=p.get("required", True),
                    location=p.get("in", "path"),
                ))

            routes.append(DocumentedRoute(
                method=method.upper(),
                path=path,
                parameters=params,
                summary=operation.get("summary"),
            ))

    logger.info("Extracted %d documented routes from OpenAPI spec", len(routes))
    return routes


def _schema_type(schema: dict[str, Any]) -> str:
    """Pull the OpenAPI type string from a schema object."""
    if not isinstance(schema, dict):
        return "string"
    return schema.get("type", "string")
