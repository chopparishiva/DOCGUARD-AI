# DocGuard AI — Backend

FastAPI backend for the DocGuard AI Autonomous API Documentation Agent.
Detects API-code changes, compares them with existing OpenAPI docs,
generates the required documentation updates, validates the result, and
reports synchronization status.

## Quick start

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the interactive Swagger UI.

## Endpoints

| Method | Path                            | Description                                    |
|--------|---------------------------------|------------------------------------------------|
| GET    | `/api/health`                   | Service health check                           |
| POST   | `/api/repositories/analyze`     | Analyse a repository (live or demo mode)       |
| GET    | `/api/analysis/{analysis_id}`   | Analysis status + detected API changes         |
| GET    | `/api/documentation/{analysis_id}` | Generated OpenAPI docs + validation result   |

## DEMO MODE (offline, deterministic)

DEMO MODE uses the built-in sample backend shipped in `demo/sample-backend/`
and needs **no network access and no LLM API**. It always produces the same
result:

```
POST /api/repositories/analyze
{
  "repository_url": "https://github.com/example/project",
  "demo_mode": true
}
```

This detects the known change:

- `GET /users` → `GET /users/{user_id}`
- parameter `user_id: integer` added

Generates the updated OpenAPI spec, validates it, and reports
`documentation_status: "synchronized"`.

## Design notes

- **Route extraction** uses Python's `ast` module, not fragile regex.
- **Change detection** is deterministic and returns structured change objects.
- **Documentation Agent** is a rule-based engine today but is designed so an
  LLM provider can be plugged in later (see `DocumentationAgent(llm_provider=...)`).
- **No database** — results are kept in an in-memory store keyed by
  `analysis_id`, which is fine for a hackathon MVP.
- **Validation** checks structure, required fields, path-prefix convention,
  supported methods, and that path params are marked required.

## Tests

```bash
cd backend
python -m unittest discover -s tests -v
```

Covers: route extraction, change detection, documentation generation,
OpenAPI validation, and the deterministic demo pipeline.

## Architecture

See `../docs/architecture.md` for the full pipeline diagram.
See `../docs/demo-script.md` for the hackathon presentation flow.