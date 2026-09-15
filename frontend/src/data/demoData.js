/**
 * DocGuard AI - Demo Mode Data
 *
 * Deterministic, offline demo data for the repository analysis workflow.
 * The scenario mirrors the backend's built-in demo repository exactly:
 *
 *   BEFORE:  GET /users
 *   AFTER:   GET /users/{user_id}
 *   Added:   user_id : integer
 *   Final:   Documentation Synchronized
 *
 * When the backend is available and LIVE analysis runs, these rows are
 * replaced with data mapped from the backend AnalysisResult
 * (see src/services/mapResult.js).
 */

export const DEMO_STEPS = [
  {
    id: 'repo',
    step: 'Git Repository',
    detail: 'Analyzed docguard-demo · 2 Python files',
    pending: 'Connecting to repository…',
  },
  {
    id: 'routes',
    step: 'API Route Detection',
    detail: '2 endpoints detected across the codebase',
    pending: 'Scanning routes…',
  },
  {
    id: 'changes',
    step: 'Change Detection',
    detail: 'GET /users → GET /users/{user_id}',
    pending: 'Detecting changes…',
  },
  {
    id: 'openapi',
    step: 'OpenAPI Comparison',
    detail: 'Compared against openapi.yaml · 1 diff',
    pending: 'Comparing specs…',
  },
  {
    id: 'agent',
    step: 'AI Documentation Agent',
    detail: 'Added user_id : integer parameter',
    pending: 'Agent drafting…',
  },
  {
    id: 'update',
    step: 'OpenAPI Update',
    detail: 'Merged 1 operation into openapi.yaml',
    pending: 'Updating spec…',
  },
  {
    id: 'validation',
    step: 'Validation',
    detail: 'OpenAPI validators passed',
    pending: 'Validating…',
  },
  {
    id: 'sync',
    step: 'Documentation Synchronized',
    detail: 'Docs in sync with source code',
    pending: 'Synchronizing…',
  },
];

/**
 * Frontend-local DEMO MODE result.
 * Deterministic and offline — no backend, no GitHub, no internet needed.
 * Returns the same shape the backend AnalysisResult uses so the rest of
 * the app can treat demo and live identically.
 */
export const DEMO_ANALYSIS = {
  mode: 'demo',
  status: 'completed',
  documentation_status: 'synchronized',
  summary: {
    routes_detected: 2,
    changes_detected: 1,
    documentation_updated: true,
    validation_passed: true,
  },
  repository: { name: 'docguard-demo' },
  changes: [
    {
      type: 'PATH_CHANGED',
      severity: 'warning',
      description: 'Path signature changed: /users → /users/{user_id}',
      before: { method: 'GET', path: '/users' },
      after: { method: 'GET', path: '/users/{user_id}' },
    },
    {
      type: 'PARAMETER_ADDED',
      severity: 'info',
      description: "Parameter 'user_id' added to GET /users/{user_id}",
      before: { method: 'GET', path: '/users/{user_id}' },
      after: { method: 'GET', path: '/users/{user_id}', parameter: 'user_id', type: 'integer', required: true },
    },
  ],
  workflow: DEMO_STEPS,
};