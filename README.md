# DocGuard AI

Autonomous API Documentation Agent — detects changes in API code, compares
them against existing OpenAPI documentation, automatically generates the
required documentation updates, validates the result, and reports
synchronization status.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐
│   Frontend   │ ─▶ │   FastAPI    │ ─▶ │  Analysis pipeline   │
│  React+Vite  │ ◀─ │   backend    │ ◀─ │   (7 service stages) │
└──────────────┘    └──────────────┘    └──────────────────────┘
```

## Repo layout

```
testing1/
├── frontend/       React + Vite frontend (hackathon demo UI)
├── backend/        FastAPI backend
├── demo/
│   └── sample-backend/   deterministic demo repo (before/after + openapi.yaml)
└── docs/
    ├── frontend-implementation.md
    ├── architecture.md
    └── demo-script.md
```

## Quick start

### 1. Backend

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

Health check: `curl http://localhost:8000/api/health`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev           # http://localhost:5173 (or 5174 if 5173 is busy)
```

### DEMO MODE analysis

The frontend uses DEMO MODE out of the box (deterministic, offline, no GitHub,
no LLM). Or call the backend directly:

```bash
curl -X POST http://localhost:8000/api/repositories/analyze \
  -H "Content-Type: application/json" \
  -d '{"repository_url":"https://github.com/example/project","demo_mode":true}'
```

## Docs

- [Architecture](docs/architecture.md)
- [Hackathon demo script](docs/demo-script.md)
- [Frontend implementation](docs/frontend-implementation.md)