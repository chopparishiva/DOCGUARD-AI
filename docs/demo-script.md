# DocGuard AI — Hackathon Demo Script

**Duration:** ~60–90 seconds. **Prerequisites:** backend running
(`uvicorn app.main:app --port 8000`), frontend running, and a browser on the
hero screen.

---

## 1. Introduce the problem (10 s)

> "API docs go stale the moment code changes. DocGuard AI watches your
> endpoints, detects what changed, and updates the OpenAPI docs for you —
> automatically."

Point at the hero: *"Keep your API docs in sync automatically."*

## 2. Show DocGuard AI (10 s)

> "This is DocGuard AI — an autonomous API documentation agent. No manual
> doc-writing. When a developer changes an endpoint, DocGuard AI detects it,
> compares it against the OpenAPI spec, and fixes the documentation."

## 3. Trigger repository analysis (5 s)

Click **Analyze Repository** (primary CTA, demo mode).

> "We're analyzing a sample repository. Watch the pipeline work."

The 8-step workflow begins animating — Git Repository → API Route Detection →
Change Detection → OpenAPI Comparison → AI Documentation Agent → OpenAPI
Update → Validation → Documentation Synchronized.

## 4. Show the detected change (15 s)

As the workflow reaches the change stages, call out the core discovery:

> "Here's what DocGuard AI found: the code now exposes `GET /users/{user_id}` —
> but the documentation still says `GET /users`. The docs are out of sync."

## 5. Show the documentation agent updating OpenAPI (10 s)

> "The AI Documentation Agent drafts the new path definition, pulling the
> `user_id: integer` parameter straight out of the Python type annotation."

## 6. Show validation (10 s)

> "Before it touches the live docs, the updated OpenAPI spec is validated —
> structure, required fields, path parameters, serialization. It passes."

## 7. Show Documentation Synchronized (10 s)

The workflow completes with **Documentation Synchronized**.

> "The docs are in sync again. Code changed, docs followed, validation passed —
> with zero manual effort."

---

## Optional live part (only if you want a second demo)

Instead of demo mode, call the live analyzer against a public FastAPI GitHub
repository. Paste the URL into the frontend's analyzer input and re-run. The
same pipeline runs for real: repository fetch → route extraction → change
detection → doc update → validation.

---

## Post-demo talking points

- **Deterministic:** demo mode produces the exact same result every run.
- **Offline-safe:** demo mode needs no GitHub access and no LLM key.
- **Honest numbers:** the demo reports the *actual* route/change counts from
  the sample repo rather than fabricated marketing stats.
- **LLM-pluggable:** the `DocumentationAgent` interface is ready for a real
  LLM provider later.
- **Clean architecture:** each pipeline stage is its own service module —
  repository fetch, route extraction, schema analysis, OpenAPI parsing, change
  detection, doc generation, validation.