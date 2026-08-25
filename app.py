from __future__ import annotations

import mimetypes
import os
import json
from pathlib import Path
from datetime import datetime, timezone

from flaxon import Flaxon
from flaxon.http.response import Response
from flaxon.jinax import Jinax

from database.connection import database
from database import repositories
from services.search_service import search
from services.ranking_service import normalize_query
from crawler.worker import crawl_batch
from crawler.canonical import canonicalize

ROOT = Path(__file__).resolve().parent
app = Flaxon("pyseek", debug=os.getenv("FLAXON_DEBUG", "false").lower() == "true")
app.use_templates(Jinax(ROOT / "templates", auto_reload=app.debug, strict_undefined=True))


def _json_error(message: str, status: int = 400):
    return Response(json.dumps({"ok": False, "error": message}).encode("utf-8"), status_code=status, media_type="application/json")


def _secret_ok(request) -> bool:
    expected = os.getenv("CRON_SECRET", "").strip()
    if not expected:
        return bool(app.debug)
    token = request.headers.get("x-cron-secret", "")
    auth = request.headers.get("authorization", "")
    return token == expected or auth == f"Bearer {expected}"


def _public_file(relative: str, media_type: str):
    target = (ROOT / "public" / relative).resolve()
    public = (ROOT / "public").resolve()
    if public not in target.parents or not target.is_file():
        return Response("Not found", status_code=404, media_type="text/plain")
    return Response(target.read_bytes(), media_type=media_type)


for file in (ROOT / "public").rglob("*") if (ROOT / "public").exists() else []:
    if file.is_file():
        relative = file.relative_to(ROOT / "public").as_posix()
        media = {".webmanifest": "application/manifest+json", ".js": "application/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".html": "text/html; charset=utf-8"}.get(file.suffix.lower(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        async def serve_asset(request, path=file, media_type=media):
            return Response(path.read_bytes(), media_type=media_type)
        app.get(f"/assets/{relative}")(serve_asset)


@app.get("/")
async def home(request):
    return await request.render("index.html", {"title": "PySeek"})


@app.get("/manifest.webmanifest")
async def manifest(request):
    return _public_file("manifest.webmanifest", "application/manifest+json")


@app.get("/sw.js")
async def service_worker(request):
    return _public_file("sw.js", "application/javascript")


@app.get("/offline.html")
async def offline(request):
    return _public_file("offline.html", "text/html; charset=utf-8")


@app.get("/api/health")
async def health():
    return {"ok": True, "service": "pyseek", "time": datetime.now(timezone.utc).isoformat(), "database_configured": not database.sqlite_mode, "storage": "sqlite" if database.sqlite_mode else "neon-postgresql"}


@app.get("/api/search")
async def api_search(request):
    query = normalize_query(request.query_params.get("q", ""))
    if not query:
        return {"ok": True, "query": "", "results": [], "total": 0}
    try:
        return {"ok": True, **search(query, domain=request.query_params.get("domain", ""))}
    except Exception as exc:
        return _json_error(f"Search index unavailable: {exc}", 503)


@app.get("/api/suggest")
async def api_suggest(request):
    query = normalize_query(request.query_params.get("q", ""))
    if len(query) < 2:
        return {"ok": True, "suggestions": []}
    try:
        return {"ok": True, "suggestions": repositories.suggestions(query)}
    except Exception as exc:
        return _json_error(f"Suggestions unavailable: {exc}", 503)


@app.get("/api/stats")
async def api_stats():
    try:
        return {"ok": True, **repositories.stats()}
    except Exception as exc:
        # Keep the shell usable before a developer configures Neon. Search
        # and crawling still return an explicit 503 because they need data.
        return {"ok": True, "database_configured": False, "documents": 0, "queued": 0, "failed": 0}


@app.post("/api/internal/seed")
async def seed(request):
    if not _secret_ok(request):
        return _json_error("Unauthorized", 401)
    payload = await request.json()
    urls = payload.get("urls", []) if isinstance(payload, dict) else []
    try:
        valid = [canonicalize(url) for url in urls[:100]]
    except (TypeError, ValueError) as exc:
        return _json_error(str(exc))
    try:
        return {"ok": True, "added": repositories.enqueue_urls(list(dict.fromkeys(valid)))}
    except Exception as exc:
        return _json_error(f"Queue unavailable: {exc}", 503)


@app.get("/api/cron/crawl")
async def cron_crawl(request):
    if not _secret_ok(request):
        return _json_error("Unauthorized", 401)
    try:
        return {"ok": True, **crawl_batch()}
    except Exception as exc:
        return _json_error(f"Crawler unavailable: {exc}", 503)


if __name__ == "__main__":
    print("PySeek: run `flaxon run app:app --reload`")
