"""
DocGuard AI — OpenAPI Validator

Validates a generated or updated OpenAPI specification document.
Returns structured results with a list of errors.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_SUPPORTED_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def validate_openapi(spec: dict[str, Any]) -> dict[str, Any]:
    """
    Validate an OpenAPI spec dict.

    Returns:
        {"valid": True, "errors": []}  on success
        {"valid": False, "errors": [...]}  on failure
    """
    errors: list[str] = []

    # 1. Top-level openapi field
    if not spec.get("openapi"):
        errors.append("Missing required 'openapi' version field")

    # 2. info block
    info = spec.get("info")
    if not info or not isinstance(info, dict):
        errors.append("Missing required 'info' object")
    else:
        if not info.get("title"):
            errors.append("Missing 'info.title'")
        if not info.get("version"):
            errors.append("Missing 'info.version'")

    # 3. paths block
    paths = spec.get("paths")
    if paths is None:
        errors.append("Missing required 'paths' object")
    elif not isinstance(paths, dict):
        errors.append("'paths' must be an object")
    else:
        for path, path_item in paths.items():
            if not path.startswith("/"):
                errors.append(f"Path '{path}' must start with '/'")

            if not isinstance(path_item, dict):
                errors.append(f"Path '{path}' must be an object")
                continue

            for method, operation in path_item.items():
                method_lower = method.lower()
                if method_lower not in _SUPPORTED_HTTP_METHODS:
                    errors.append(f"Unsupported HTTP method '{method}' on path '{path}'")
                    continue

                if not isinstance(operation, dict):
                    errors.append(f"Operation '{method}' on '{path}' must be an object")
                    continue

                # Check responses exist
                if "responses" not in operation:
                    errors.append(f"Missing 'responses' in {method.upper()} {path}")

                # Check parameter definitions
                for param in operation.get("parameters", []):
                    if not isinstance(param, dict):
                        errors.append(f"Parameter in {method.upper()} {path} must be an object")
                        continue
                    if not param.get("name"):
                        errors.append(f"Parameter missing 'name' in {method.upper()} {path}")
                    if not param.get("in"):
                        errors.append(f"Parameter missing 'in' in {method.upper()} {path}")

                    # Path parameters must be required
                    if param.get("in") == "path" and not param.get("required", False):
                        errors.append(
                            f"Path parameter '{param.get('name')}' in {method.upper()} {path} "
                            f"must be marked as required"
                        )

    # 4. Serialization check
    try:
        json.dumps(spec)
    except (TypeError, ValueError) as exc:
        errors.append(f"Spec is not JSON-serializable: {exc}")

    valid = len(errors) == 0
    logger.info("OpenAPI validation: %s (%d errors)", "passed" if valid else "failed", len(errors))
    return {"valid": valid, "errors": errors}
