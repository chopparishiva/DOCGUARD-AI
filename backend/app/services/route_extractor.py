"""
DocGuard AI — Route Extractor

Parses Python source files with the `ast` module to detect FastAPI
route decorators and extract structured endpoint information.
"""
from __future__ import annotations

import ast
import logging
from typing import Optional

from ..models.schemas import DetectedRoute, RouteParameter

logger = logging.getLogger(__name__)

# Decorator names we recognise
_ROUTE_METHODS = {"get", "post", "put", "patch", "delete"}
# Common FastAPI object names for app/router instances.
_ROUTE_OBJECT_NAMES = {"app", "router", "application", "api", "api_router"}


def _is_route_object(name: str) -> bool:
    """Heuristic: is this object likely a FastAPI app/router instance?"""
    n = name.lower()
    if n in _ROUTE_OBJECT_NAMES:
        return True
    return any(n.endswith(s) for s in ("_app", "_router", "_api", "application"))


def _extract_path_from_decorator(decorator: ast.expr) -> Optional[str]:
    """Return the first string argument of a decorator call, or None."""
    if not isinstance(decorator, ast.Call):
        return None
    # First positional arg
    if decorator.args:
        arg = decorator.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    # keyword arg "path" or "url"
    for kw in decorator.keywords or []:
        if kw.arg in ("path", "url") and isinstance(kw.value, ast.Constant):
            return kw.value.value
    return None


def _get_decorator_name(decorator: ast.expr) -> Optional[tuple[str, str]]:
    """Return (object_name, method) for something like  @app.get  or  @router.post."""
    attr = None
    if isinstance(decorator, ast.Attribute):
        attr = decorator.attr
        if isinstance(decorator.value, ast.Name):
            obj_name = decorator.value.id
        else:
            return None
    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        attr = decorator.func.attr
        if isinstance(decorator.func.value, ast.Name):
            obj_name = decorator.func.value.id
        else:
            return None
    else:
        return None

    if attr not in _ROUTE_METHODS:
        return None
    if not _is_route_object(obj_name):
        return None
    return (obj_name, attr.upper())


def _map_python_type(annotation: Optional[ast.expr]) -> str:
    """Map a Python type annotation AST node to an OpenAPI type string."""
    if annotation is None:
        return "string"
    if isinstance(annotation, ast.Name):
        return {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "List": "array",
            "dict": "object",
            "Dict": "object",
        }.get(annotation.id, "string")
    if isinstance(annotation, ast.Subscript):
        # e.g. list[int] → array
        base = _map_python_type(annotation.value)
        return base
    if isinstance(annotation, ast.Constant):
        return "string"
    return "string"


def _extract_params_from_args(func: ast.FunctionDef, path: str = "") -> list[RouteParameter]:
    """Extract params from function signature, skipping 'self'/'cls'.

    Args that appear in the path template (e.g. {user_id}) are path params;
    everything else is a query param (the FastAPI convention for non-path args).
    """
    params: list[RouteParameter] = []
    defaults_map: dict[str, Optional[ast.expr]] = {}

    # Build defaults map (positional defaults align from the end)
    args = func.args
    n_defaults = len(args.defaults)
    n_args = len(args.args)
    for i, d in enumerate(args.defaults):
        defaults_map[args.args[n_args - n_defaults + i].arg] = d

    for arg in args.args:
        if arg.arg in ("self", "cls"):
            continue
        has_default = arg.arg in defaults_map
        is_path_param = "{" + arg.arg + "}" in path

        if is_path_param:
            location = "path"
            required = True
        else:
            location = "query"
            required = not has_default

        params.append(RouteParameter(
            name=arg.arg,
            type=_map_python_type(arg.annotation),
            required=required,
            location=location,
        ))
    return params


def extract_routes_from_source(source: str, filename: str = "") -> list[DetectedRoute]:
    """Parse a Python source string and return detected FastAPI routes."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logger.warning("Syntax error parsing %s: %s", filename, exc)
        return []

    routes: list[DetectedRoute] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for dec in node.decorator_list:
            info = _get_decorator_name(dec)
            if info is None:
                continue
            path = _extract_path_from_decorator(dec)
            if path is None:
                continue

            method_name = info[1]
            params = _extract_params_from_args(node, path=path)

            routes.append(DetectedRoute(
                method=method_name,
                path=path,
                function_name=node.name,
                parameters=params,
                source_file=filename,
            ))

    logger.info("Extracted %d routes from %s", len(routes), filename or "<source>")
    return routes
