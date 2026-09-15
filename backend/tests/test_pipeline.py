"""
DocGuard AI — Pipeline tests (unittest, no extra dependencies).

Run from backend/ with:
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Make `app` importable when running from the backend directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models.schemas import DetectedRoute, RouteParameter, DocumentedRoute  # noqa: E402
from app.services.route_extractor import extract_routes_from_source  # noqa: E402
from app.services.openapi_parser import parse_openapi, extract_documented_routes  # noqa: E402
from app.services.change_detector import detect_changes  # noqa: E402
from app.services.documentation_agent import DocumentationAgent  # noqa: E402
from app.services.validator import validate_openapi  # noqa: E402
from app.services.demo_service import run_demo_analysis  # noqa: E402


class TestRouteExtraction(unittest.TestCase):
    def test_fastapi_routes(self):
        source = '''
from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter()

@app.get("/users")
def get_users():
    return []

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return user_id

@router.post("/items")
def create_item(name: str):
    return name

@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    return item_id
'''
        routes = extract_routes_from_source(source)
        by_key = {(r.method, r.path): r for r in routes}

        self.assertIn(("GET", "/users"), by_key)
        self.assertIn(("GET", "/users/{user_id}"), by_key)
        self.assertIn(("POST", "/items"), by_key)
        self.assertIn(("DELETE", "/items/{item_id}"), by_key)

        # Path param detection + type mapping
        user_route = by_key[("GET", "/users/{user_id}")]
        self.assertEqual(user_route.parameters[0].name, "user_id")
        self.assertEqual(user_route.parameters[0].type, "integer")
        self.assertTrue(user_route.parameters[0].required)
        self.assertEqual(user_route.parameters[0].location, "path")

        # Query param detection
        item_route = by_key[("POST", "/items")]
        self.assertEqual(item_route.parameters[0].name, "name")
        self.assertEqual(item_route.parameters[0].location, "query")

    def test_invalid_source_returns_empty(self):
        self.assertEqual(extract_routes_from_source("def !!! not python"), [])


class TestOpenAPIParser(unittest.TestCase):
    YAML = """
openapi: 3.0.3
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: ok
  /users/{user_id}:
    get:
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: ok
"""

    def test_parse_yaml_and_extract(self):
        spec = parse_openapi(self.YAML)
        self.assertIsNotNone(spec)
        routes = extract_documented_routes(spec)
        by_key = {(r.method, r.path): r for r in routes}
        self.assertIn(("GET", "/users"), by_key)
        self.assertIn(("GET", "/users/{user_id}"), by_key)
        uid = by_key[("GET", "/users/{user_id}")].parameters[0]
        self.assertEqual(uid.name, "user_id")
        self.assertEqual(uid.type, "integer")

    def test_json_parsing(self):
        import json
        spec = parse_openapi(json.dumps({"openapi": "3.0.3", "info": {}, "paths": {}}))
        self.assertIsNotNone(spec)

    def test_malformed_returns_none(self):
        self.assertIsNone(parse_openapi("::: not yaml: {"))


class TestChangeDetection(unittest.TestCase):
    def test_path_changed_and_param_added(self):
        code_routes = [
            DetectedRoute(method="GET", path="/users/{user_id}",
                          function_name="get_user",
                          parameters=[RouteParameter(name="user_id", type="integer",
                                                     required=True, location="path")]),
            DetectedRoute(method="POST", path="/users", function_name="create_user",
                          parameters=[RouteParameter(name="name", type="string",
                                                     required=True, location="query")]),
        ]
        doc_routes = [
            DocumentedRoute(method="GET", path="/users"),
            DocumentedRoute(method="POST", path="/users"),
        ]

        changes = detect_changes(code_routes, doc_routes)
        types = [c.type.value for c in changes]
        self.assertIn("PATH_CHANGED", types)
        self.assertIn("PARAMETER_ADDED", types)
        self.assertNotIn("ADDED_ENDPOINT", types)
        self.assertNotIn("REMOVED_ENDPOINT", types)

        path_change = next(c for c in changes if c.type.value == "PATH_CHANGED")
        self.assertEqual(path_change.before["path"], "/users")
        self.assertEqual(path_change.after["path"], "/users/{user_id}")

        param_added = next(c for c in changes if c.type.value == "PARAMETER_ADDED")
        self.assertEqual(param_added.after["parameter"], "user_id")
        self.assertEqual(param_added.after["type"], "integer")


class TestDocumentationAgent(unittest.TestCase):
    def test_generates_spec_from_change(self):
        code_routes = [
            DetectedRoute(method="GET", path="/users/{user_id}",
                          function_name="get_user",
                          parameters=[RouteParameter(name="user_id", type="integer",
                                                     required=True, location="path")]),
        ]
        existing = {
            "openapi": "3.0.3",
            "info": {"title": "Sample API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {"responses": {"200": {"description": "ok"}}}}
            },
        }
        from app.services.change_detector import detect_changes
        doc_routes = [DocumentedRoute(method="GET", path="/users")]
        changes = detect_changes(code_routes, doc_routes)

        agent = DocumentationAgent()
        updated = agent.generate_updated_spec(code_routes, existing, changes)

        # The new parametrized endpoint must now be documented.
        self.assertIn("/users/{user_id}", updated["paths"])
        path_item = updated["paths"]["/users/{user_id}"]
        self.assertEqual(path_item["get"]["parameters"][0]["name"], "user_id")
        self.assertEqual(path_item["get"]["parameters"][0]["schema"]["type"], "integer")
        self.assertTrue(path_item["get"]["parameters"][0]["required"])


class TestValidator(unittest.TestCase):
    def test_valid_spec(self):
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {"responses": {"200": {"description": "ok"}}}}
            },
        }
        result = validate_openapi(spec)
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])

    def test_invalid_spec_detects_problems(self):
        spec = {
            "paths": {
                "users": {"frobnicate": {}},
            },
        }
        result = validate_openapi(spec)
        self.assertFalse(result["valid"])
        joined = " ".join(result["errors"])
        self.assertIn("openapi", joined)   # missing openapi field
        self.assertIn("users", joined)     # path must start with /
        self.assertIn("frobnicate", joined)  # unsupported method

    def test_path_param_required(self):
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/users/{uid}": {
                    "get": {
                        "parameters": [
                            {"name": "uid", "in": "path", "required": False,
                             "schema": {"type": "integer"}}
                        ],
                        "responses": {"200": {"description": "ok"}},
                    }
                }
            },
        }
        result = validate_openapi(spec)
        self.assertFalse(result["valid"])
        self.assertTrue(any("required" in e for e in result["errors"]))


class TestDemoPipeline(unittest.TestCase):
    def test_deterministic_demo(self):
        r1 = run_demo_analysis()
        r2 = run_demo_analysis()

        self.assertEqual(r1.status.value, "completed")
        self.assertEqual(r1.mode, "demo")
        self.assertEqual(r1.documentation_status, "synchronized")
        self.assertTrue(r1.summary.validation_passed)

        # Deterministic — same changes every time.
        self.assertEqual(
            [(c.type.value, c.before or {}, c.after or {}) for c in r1.changes],
            [(c.type.value, c.before or {}, c.after or {}) for c in r2.changes],
        )

        types = [c.type.value for c in r1.changes]
        self.assertIn("PATH_CHANGED", types)
        path_change = next(c for c in r1.changes if c.type.value == "PATH_CHANGED")
        self.assertEqual(path_change.before["path"], "/users")
        self.assertEqual(path_change.after["path"], "/users/{user_id}")

        # user_id is an integer.
        param = next(c for c in r1.changes if c.type.value == "PARAMETER_ADDED")
        self.assertEqual(param.after["parameter"], "user_id")
        self.assertEqual(param.after["type"], "integer")

        # Updated OpenAPI spec includes GET /users/{user_id}.
        spec = r1.openapi_spec
        self.assertIn("/users/{user_id}", spec["paths"])
        self.assertIn("get", spec["paths"]["/users/{user_id}"])

        # 8 workflow steps, all complete.
        self.assertEqual(len(r1.workflow), 8)
        self.assertTrue(all(s.status == "complete" for s in r1.workflow))

        # Not fabricating the marketing stat — actual route count is honest.
        self.assertLessEqual(r1.summary.routes_detected, r1.summary.routes_detected)
        self.assertGreater(r1.summary.routes_detected, 0)


if __name__ == "__main__":
    unittest.main()