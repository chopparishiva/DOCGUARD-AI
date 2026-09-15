# DocGuard AI — Architecture

DocGuard AI detects changes in API code, compares them with existing OpenAPI
documentation, automatically generates the required documentation updates,
validates the result, and reports synchronization status.

## System overview

```
┌────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                   │
│  · Hero / workflow visualization (DEMO MODE ready)         │
│  · Calls the backend when API analysis is triggered        │
└──────────────────────────┬─────────────────────────────────┘
                           │  HTTP (JSON)
┌──────────────────────────▼─────────────────────────────────┐
│  FastAPI (backend/app/main.py)                             │
│  · CORS for local Vite dev servers                         │
│  · Routes: /api/health, /api/repositories/analyze,         │
│            /api/analysis/{id}, /api/documentation/{id}     │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  Repository Service (github_service.py)                    │
│  · Validate GitHub URLs · fetch file tree & contents       │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  Route Extractor (route_extractor.py)                      │
│  · AST-based FastAPI decorator detection                   │
│  · GET / POST / PUT / PATCH / DELETE                       │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  Schema Analyzer (schema_analyzer.py)                      │
│  · Python → OpenAPI type mapping (int → integer, …)        │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  OpenAPI Parser (openapi_parser.py)                        │
│  · JSON + YAML · normalised documented-route extraction    │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  Change Detector (change_detector.py)                      │
│  · code routes vs documented routes                        │
│  · ADDED / REMOVED / PATH_CHANGED / PARAMETER_* changes    │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  Documentation Agent (documentation_agent.py)              │
│  · rule-based OpenAPI generation (LLM-pluggable later)     │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  Validator (validator.py)                                  │
│  · structural checks · path params required · serializable │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│  Result: analysis summary + changes + updated OpenAPI      │
│          + workflow steps + documentation_status           │
└────────────────────────────────────────────────────────────┘
```

## Pipeline stages

1. **Repository Fetching** — `github_service` validates the URL, lists the
   default-branch tree, and locates `.py` files and `openapi.{json,yaml,yml}`.
   Network failures degrade cleanly to structured errors; the app never crashes.
2. **API Route Extraction** — `route_extractor` parses Python with the `ast`
   module (no fragile regex), finds `@app.get / @router.post / …` decorators
   and builds structured routes with method, path, function name, and params.
3. **Schema Analysis** — `schema_analyzer` maps Python annotations to OpenAPI
   types (`str→string`, `int→integer`, `float→number`, `bool→boolean`,
   `list→array`).
4. **OpenAPI Parsing** — `openapi_parser` reads JSON or YAML specs and
   normalises them into documented routes for comparison.
5. **Change Detection** — `change_detector` compares code routes to documented
   routes and reports structured changes: `ADDED_ENDPOINT`, `REMOVED_ENDPOINT`,
   `PATH_CHANGED`, `PARAMETER_ADDED`, `PARAMETER_REMOVED`,
   `PARAMETER_TYPE_CHANGED`. Path-signature changes (`/users` →
   `/users/{user_id}`) are detected first so they surface as a single change.
6. **Documentation Agent** — `documentation_agent.DocumentationAgent`
   deterministically generates the updated OpenAPI paths from the detected
   routes. The constructor accepts `llm_provider` so an LLM can be plugged in
   later without changing the public `generate_updated_spec(...)` interface —
   but no LLM is required.
7. **Validation** — `validator` checks: `openapi` and `info` exist, `paths`
   exists, every path starts with `/`, supported HTTP methods, parameters have
   required fields, path parameters are required, and the document serializes
   to JSON.

## Deterministic DEMO MODE

The frontend's 8-step workflow drives the built-in demo. The backend mirrors
exactly the same steps:

1. Git Repository
2. API Route Detection
3. Change Detection
4. OpenAPI Comparison
5. AI Documentation Agent
6. OpenAPI Update
7. Validation
8. Documentation Synchronized

The demo scenario uses the sample backend in `demo/sample-backend/`:

- `before/main.py`    — original code with `GET /users`
- `after/main.py`     — new code with `GET /users/{user_id}`
- `openapi.yaml`       — existing docs that still only describe `GET /users`

When `demo_mode: true` is sent to `/api/repositories/analyze`, the backend
runs the **same pipeline services** against the sample sources: it parses
`after/main.py`, extracts `GET /users/{user_id}`, detects the change against
the docs, regenerates the OpenAPI spec, validates it, and returns
`documentation_status: "synchronized"`. No network, no LLM, no randomness, no
database — identical output on every run.

## Data flow for an analysis

`POST /api/repositories/analyze` → `AnalysisResult`
`GET /api/analysis/{analysis_id}` → same `AnalysisResult` (retrieved from the
in-memory store)
`GET /api/documentation/{analysis_id}` → `DocumentationResponse` containing the
generated OpenAPI spec and validation result.

## Error handling

- Invalid GitHub URL → 422 with a readable message.
- Network failure / repo not found → 422 "Could not fetch repository tree…".
- No Python files → 422 "No Python files found…".
- Malformed / missing OpenAPI → logged and handled (docs generated from
  scratch); never crashes the pipeline.
- Stack traces are never surfaced to API clients.