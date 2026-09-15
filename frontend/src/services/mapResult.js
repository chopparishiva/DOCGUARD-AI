// ============================================================
// DocGuard AI — backend result → workflow mapper
// ============================================================
// Converts a FastAPI AnalysisResult into the rows the DemoWorkflow
// component renders, plus a small display object. Handles both the
// real backend schema and the frontend-local DEMO payload — they
// share the same shape.

import { DEMO_STEPS } from '../data/demoData';

const STEP_NAMES = [
  'Git Repository',
  'API Route Detection',
  'Change Detection',
  'OpenAPI Comparison',
  'AI Documentation Agent',
  'OpenAPI Update',
  'Validation',
  'Documentation Synchronized',
];

function plural(n) {
  return n === 1 ? '' : 's';
}

function openapiFileName(result) {
  const repo = result?.repository;
  return repo?.openapi_file || 'openapi.yaml';
}

/**
 * Build a change line like "GET /users → GET /users/{user_id}" from the
 * backend changes array, or null if there is no path-affecting change.
 */
export function describePrimaryChange(changes = []) {
  const pathChange = changes.find((c) => c?.type === 'PATH_CHANGED');
  if (pathChange?.before?.path && pathChange?.after?.path) {
    return `${pathChange.before.method || 'GET'} ${pathChange.before.path} → ${pathChange.after.method || 'GET'} ${pathChange.after.path}`;
  }
  const added = changes.find((c) => c?.type === 'ADDED_ENDPOINT');
  if (added?.after?.path) {
    return `+ ${added.after.method || 'GET'} ${added.after.path}`;
  }
  const removed = changes.find((c) => c?.type === 'REMOVED_ENDPOINT');
  if (removed?.before?.path) {
    return `− ${removed.before.method || 'GET'} ${removed.before.path}`;
  }
  return null;
}

/**
 * Describe an added/first parameter, e.g. "user_id : integer".
 */
export function describeAddedParameter(changes = []) {
  const added = changes.find((c) => c?.type === 'PARAMETER_ADDED');
  if (added?.after?.parameter) {
    const type = added.after.type || 'string';
    return `${added.after.parameter} : ${type}`;
  }
  return null;
}

/**
 * Map a backend AnalysisResult into 8 workflow rows for DemoWorkflow.
 * Uses the backend `workflow` array when present; otherwise derives rows
 * from the summary. Always returns exactly 8 rows matching STEP_NAMES.
 */
export function mapAnalysisToWorkflow(result) {
  const summary = result?.summary || {};
  const nRoutes = summary.routes_detected ?? result?.routes?.length ?? 0;
  const nChanges = summary.changes_detected ?? result?.changes?.length ?? 0;
  const valid = summary.validation_passed !== false;
  const repoName = result?.repository?.name || 'repository';
  const nPyFiles = result?.repository?.python_files ?? result?.repository?.files_scanned ?? 0;

  const changeLine = describePrimaryChange(result?.changes) || `${nChanges} change${plural(nChanges)} detected`;
  const paramLine = describeAddedParameter(result?.changes);
  const docName = openapiFileName(result);

  // Respect backend-provided workflow steps where present.
  const backendWorkflow = Array.isArray(result?.workflow)
    ? result.workflow.filter((s) => s && s.step)
    : [];

  const pending = 'Processing…';
  const rows = [
    {
      id: 'repo',
      step: STEP_NAMES[0],
      detail: nPyFiles
        ? `Analyzed ${repoName} · ${nPyFiles} Python file${plural(nPyFiles)}`
        : `Analyzed ${repoName}`,
      pending,
    },
    {
      id: 'routes',
      step: STEP_NAMES[1],
      detail: `${nRoutes} endpoint${plural(nRoutes)} detected across the codebase`,
      pending,
    },
    {
      id: 'changes',
      step: STEP_NAMES[2],
      detail: changeLine,
      pending,
    },
    {
      id: 'openapi',
      step: STEP_NAMES[3],
      detail: `Compared against ${docName} · ${nChanges} diff${plural(nChanges)}`,
      pending,
    },
    {
      id: 'agent',
      step: STEP_NAMES[4],
      detail: paramLine ? `Added ${paramLine} parameter` : `Drafted patches for ${nChanges} changed endpoint${plural(nChanges)}`,
      pending,
    },
    {
      id: 'update',
      step: STEP_NAMES[5],
      detail: `Merged ${nChanges} operation${plural(nChanges)} into ${docName}`,
      pending,
    },
    {
      id: 'validation',
      step: STEP_NAMES[6],
      detail: valid ? 'OpenAPI validators passed' : 'OpenAPI validation failed',
      pending,
    },
    {
      id: 'sync',
      step: STEP_NAMES[7],
      detail: valid ? 'Docs in sync with source code' : 'Docs out of sync — see validation report',
      pending,
    },
  ];

  // Overlay any backend workflow details (they may be richer than our defaults).
  if (backendWorkflow.length) {
    rows.forEach((row) => {
      const match = backendWorkflow.find((s) => s.step === row.step || s.id === row.id);
      if (match && typeof match.detail === 'string' && match.detail) {
        row.detail = match.detail;
      }
    });
  }

  return rows;
}

/**
 * Client-side validation of a GitHub repository URL before round-tripping
 * to the backend. Returns a message string, or null when the URL is OK.
 */
export function validateRepositoryUrl(url) {
  if (!url || !url.trim()) return 'Enter a GitHub repository URL.';
  const trimmed = url.trim();
  if (!/^https?:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+/.test(trimmed)) {
    return 'Enter a full GitHub URL, e.g. https://github.com/owner/repo';
  }
  return null;
}

/** True when the result came from the deterministic demo. */
export function isDemoResult(result) {
  return result?.mode === 'demo';
}