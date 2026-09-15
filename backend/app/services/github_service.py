"""
DocGuard AI — GitHub Service

Handles repository URL validation, file fetching from public GitHub repos,
and locating Python source files and OpenAPI specs.  In DEMO MODE all I/O
is bypassed — deterministic sample data is returned instead.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ---------- URL validation ----------

_GH_URL_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/|$)"
)


def parse_github_url(url: str) -> Optional[tuple[str, str]]:
    """Return (owner, repo) from a GitHub URL or None."""
    m = _GH_URL_RE.match(url.strip())
    return (m.group(1), m.group(2)) if m else None


def validate_url(url: str) -> bool:
    return parse_github_url(url) is not None


# ---------- GitHub API helpers ----------

_API = "https://api.github.com"


async def _get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """GET a JSON endpoint; return None on any failure."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers or {})
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("GitHub GET %s failed: %s", url, exc)
        return None


async def fetch_repo_tree(owner: str, repo: str) -> list[dict[str, str]]:
    """Return the full file tree of the default branch as [{path, type}]."""
    data = await _get_json(f"{_API}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1")
    if not data:
        return []
    return [item for item in data.get("tree", []) if item.get("type") == "blob"]


async def fetch_file_content(owner: str, repo: str, path: str) -> Optional[str]:
    """Fetch raw file content from the default branch."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:
        logger.warning("Failed to fetch %s/%s/%s: %s", owner, repo, path, exc)
        return None


# ---------- Convenience ----------

def find_python_files(tree: list[dict[str, str]]) -> list[str]:
    return [item["path"] for item in tree if item["path"].endswith(".py")]


def find_openapi_files(tree: list[dict[str, str]]) -> list[str]:
    names = {"openapi.json", "openapi.yaml", "openapi.yml", "swagger.json", "swagger.yaml"}
    return [item["path"] for item in tree if item["path"].rsplit("/", 1)[-1] in names]
