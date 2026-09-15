// ============================================================
// DocGuard AI — API client
// ============================================================
// Thin service abstraction for the FastAPI backend. All fetch calls
// live here — never inside visual components.
//
// The frontend continues to work in DEMO MODE even when the backend
// is offline: callers that fail (network / timeout) throw, and App
// falls back to the deterministic local demo.
//
//   analyzeRepository(url, { demoMode })  → POST /api/repositories/analyze
//   getAnalysisStatus(analysisId)          → GET  /api/analysis/{id}
//   getDocumentation(analysisId)           → GET  /api/documentation/{id}
//   checkHealth()                          → GET  /api/health

export const DEFAULT_API_BASE_URL = 'http://localhost:8000';

// Configurable via VITE_API_BASE_URL (see frontend/.env.example).
export function getApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;
}

const API_BASE = getApiBaseUrl();

// Default per-request timeout (ms) so a dead backend can never hang the UI.
const DEFAULT_TIMEOUT_MS = 15000;

async function request(path, { timeoutMs = DEFAULT_TIMEOUT_MS, ...options } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      ...options,
    });
    if (!res.ok) {
      let detail = `Request failed (HTTP ${res.status})`;
      try {
        const body = await res.json();
        if (body && typeof body.detail === 'string') detail = body.detail;
      } catch {
        /* non-JSON body — keep generic message */
      }
      const err = new Error(detail);
      err.status = res.status;
      throw err;
    }
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

// POST /api/repositories/analyze
// demoMode: true  → deterministic offline demo analysis (built-in repo).
// demoMode: false → live GitHub repository analysis.
export async function analyzeRepository(repositoryUrl, { demoMode = true } = {}) {
  return request('/api/repositories/analyze', {
    method: 'POST',
    body: JSON.stringify({
      repository_url: repositoryUrl || null,
      demo_mode: demoMode,
    }),
  });
}

// GET /api/analysis/{analysisId} — analysis status + detected changes.
export async function getAnalysisStatus(analysisId) {
  return request(`/api/analysis/${analysisId}`);
}

// GET /api/documentation/{analysisId} — generated OpenAPI + validation.
export async function getDocumentation(analysisId) {
  return request(`/api/documentation/${analysisId}`);
}

// GET /api/health — short timeout, used to detect backend availability.
export async function checkHealth() {
  return request('/api/health', { timeoutMs: 4000 });
}