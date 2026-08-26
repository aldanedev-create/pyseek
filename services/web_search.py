"""Optional Google Custom Search fallback.

The local PySeek index remains the primary source. This module is only active
when both Google CSE credentials are configured in the server environment.
"""

from __future__ import annotations

import os
import time
from urllib.parse import urlsplit, urlunsplit

import httpx

from services.ranking_service import normalize_query

GOOGLE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
_cache: dict[tuple[str, str], tuple[float, list[dict]]] = {}


def enabled() -> bool:
    return bool(os.getenv("GOOGLE_CSE_API_KEY", "").strip() and os.getenv("GOOGLE_CSE_ID", "").strip())


def _canonical_url(value: str) -> str:
    parts = urlsplit(value.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/") or "/", "", ""))


def _domain(value: str) -> str:
    return (urlsplit(value).hostname or "").lower()


def _from_google(item: dict) -> dict | None:
    link = str(item.get("link", "")).strip()
    if not link.startswith(("http://", "https://")):
        return None
    return {
        "id": f"google:{_canonical_url(link)}",
        "url": link,
        "title": str(item.get("title", "")).strip() or link,
        "description": str(item.get("snippet", "")).strip(),
        "domain": _domain(link),
        "fetched_at": None,
        "score": 0,
        "snippet": str(item.get("htmlSnippet", item.get("snippet", ""))),
        "source": "web",
    }


async def search_web(query: str, domain: str = "", limit: int = 10) -> list[dict]:
    """Fetch a bounded web result set, returning [] when disabled/unavailable."""
    query = normalize_query(query)
    domain = domain.strip().lower()
    if not query or not enabled():
        return []
    limit = max(1, min(int(limit), 10))
    cache_key = (query, domain)
    now = time.monotonic()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < 60:
        return [dict(item) for item in cached[1]]

    params = {
        "key": os.environ["GOOGLE_CSE_API_KEY"].strip(),
        "cx": os.environ["GOOGLE_CSE_ID"].strip(),
        "q": query,
        "num": limit,
        "safe": "active",
    }
    if domain:
        params["siteSearch"] = domain
        params["siteSearchFilter"] = "i"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0), follow_redirects=True) as client:
            response = await client.get(GOOGLE_ENDPOINT, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError, KeyError):
        return []

    results = [result for item in payload.get("items", []) if (result := _from_google(item))]
    _cache[cache_key] = (now, results)
    return [dict(item) for item in results]
