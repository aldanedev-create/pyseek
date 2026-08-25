from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from .connection import database

def search_documents(query: str, limit: int = 20, offset: int = 0, domain: str = "") -> list[dict[str, Any]]:
    database.ensure_schema()
    if database.sqlite_mode:
        terms = [term for term in query.split() if term]
        clauses, params = [], []
        for term in terms:
            pattern = f"%{term}%"
            clauses.append("(title LIKE ? OR description LIKE ? OR body_text LIKE ?)")
            params.extend([pattern, pattern, pattern])
        sql = "SELECT id, url, title, description, body_text, domain, fetched_at, 1.0 AS score FROM documents WHERE " + (" AND ".join(clauses) or "1=0")
        if domain:
            sql += " AND domain = ?"; params.append(domain.lower().strip())
        sql += " ORDER BY fetched_at DESC LIMIT ? OFFSET ?"; params.extend([max(1, min(limit, 50)), max(0, offset)])
        with database.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
    sql = "SELECT id, url, title, description, body_text, domain, fetched_at, ts_rank(search_vector, websearch_to_tsquery('simple', %s)) AS score FROM documents WHERE search_vector @@ websearch_to_tsquery('simple', %s)"
    params: list[Any] = [query, query]
    if domain: sql += " AND domain = %s"; params.append(domain.lower().strip())
    sql += " ORDER BY score DESC, fetched_at DESC NULLS LAST LIMIT %s OFFSET %s"; params.extend([max(1, min(limit, 50)), max(0, offset)])
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params); columns = [d.name for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

def suggestions(prefix: str, limit: int = 8) -> list[str]:
    database.ensure_schema()
    with database.connect() as conn:
        if database.sqlite_mode:
            rows = conn.execute("SELECT DISTINCT title FROM documents WHERE title LIKE ? ORDER BY title LIMIT ?", (prefix + "%", limit)).fetchall()
            return [row[0] for row in rows if row[0]]
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT title FROM documents WHERE title ILIKE %s ORDER BY title LIMIT %s", (prefix + "%", limit)); return [row[0] for row in cur.fetchall() if row[0]]

def save_document(document: dict[str, Any]) -> None:
    database.ensure_schema()
    values = (document["url"], document["canonical_url"], document.get("title", ""), document.get("description", ""), document.get("text", ""), document.get("domain", ""), document.get("fetched_at", datetime.now(timezone.utc)), document.get("status_code", 200))
    with database.connect() as conn:
        if database.sqlite_mode:
            conn.execute("INSERT INTO documents (url, canonical_url, title, description, body_text, domain, fetched_at, status_code) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(canonical_url) DO UPDATE SET url=excluded.url, title=excluded.title, description=excluded.description, body_text=excluded.body_text, domain=excluded.domain, fetched_at=excluded.fetched_at, status_code=excluded.status_code", (*values[:6], str(values[6]), values[7])); return
        with conn.cursor() as cur:
            cur.execute("INSERT INTO documents (url, canonical_url, title, description, body_text, domain, fetched_at, status_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (canonical_url) DO UPDATE SET url=EXCLUDED.url, title=EXCLUDED.title, description=EXCLUDED.description, body_text=EXCLUDED.body_text, domain=EXCLUDED.domain, fetched_at=EXCLUDED.fetched_at, status_code=EXCLUDED.status_code", values)

def enqueue_urls(urls: list[str], source_url: str = "") -> int:
    database.ensure_schema(); added = 0
    with database.connect() as conn:
        for url in urls:
            domain = url.split("/", 3)[2].split(":", 1)[0] if "://" in url else ""
            if database.sqlite_mode: added += conn.execute("INSERT OR IGNORE INTO crawl_queue (url, source_url, domain) VALUES (?,?,?)", (url, source_url, domain)).rowcount
            else:
                with conn.cursor() as cur: cur.execute("INSERT INTO crawl_queue (url, source_url, domain) VALUES (%s,%s,%s) ON CONFLICT (url) DO NOTHING", (url, source_url, domain)); added += cur.rowcount
    return added

def claim_batch(limit: int) -> list[dict[str, Any]]:
    database.ensure_schema()
    with database.connect() as conn:
        if database.sqlite_mode:
            rows = conn.execute("SELECT id, url, attempts FROM crawl_queue WHERE status='queued' AND datetime(next_attempt_at) <= datetime('now') ORDER BY priority DESC, id LIMIT ?", (max(1, min(limit, 50)),)).fetchall(); result=[]
            for row in rows: conn.execute("UPDATE crawl_queue SET status='working', locked_at=datetime('now'), attempts=attempts+1 WHERE id=?", (row[0],)); result.append({"id": row[0], "url": row[1], "attempts": row[2]+1})
            return result
        with conn.cursor() as cur:
            cur.execute("WITH picked AS (SELECT id FROM crawl_queue WHERE status='queued' AND next_attempt_at <= now() ORDER BY priority DESC, id LIMIT %s FOR UPDATE SKIP LOCKED) UPDATE crawl_queue q SET status='working', locked_at=now(), attempts=attempts+1 FROM picked WHERE q.id=picked.id RETURNING q.id, q.url, q.attempts", (max(1, min(limit, 50)),)); return [{"id": r[0], "url": r[1], "attempts": r[2]} for r in cur.fetchall()]

def finish_queue_item(item_id: int, ok: bool, error: str = "") -> None:
    database.ensure_schema()
    with database.connect() as conn:
        if database.sqlite_mode:
            if ok: conn.execute("UPDATE crawl_queue SET status='done', last_error=NULL, locked_at=NULL WHERE id=?", (item_id,))
            else: conn.execute("UPDATE crawl_queue SET status=CASE WHEN attempts >= 4 THEN 'failed' ELSE 'queued' END, next_attempt_at=datetime('now', '+' || (attempts * 60) || ' seconds'), last_error=?, locked_at=NULL WHERE id=?", (error[:1000], item_id))
            return
        with conn.cursor() as cur:
            if ok: cur.execute("UPDATE crawl_queue SET status='done', last_error=NULL, locked_at=NULL WHERE id=%s", (item_id,))
            else: cur.execute("UPDATE crawl_queue SET status=CASE WHEN attempts >= 4 THEN 'failed' ELSE 'queued' END, next_attempt_at=now() + (interval '1 minute' * attempts), last_error=%s, locked_at=NULL WHERE id=%s", (error[:1000], item_id))

def stats() -> dict[str, int]:
    database.ensure_schema()
    with database.connect() as conn:
        if database.sqlite_mode:
            row = conn.execute("SELECT (SELECT count(*) FROM documents), (SELECT count(*) FROM crawl_queue WHERE status='queued'), (SELECT count(*) FROM crawl_queue WHERE status='failed')").fetchone(); return {"documents": row[0], "queued": row[1], "failed": row[2]}
        with conn.cursor() as cur:
            cur.execute("SELECT (SELECT count(*) FROM documents), (SELECT count(*) FROM crawl_queue WHERE status='queued'), (SELECT count(*) FROM crawl_queue WHERE status='failed')"); docs, queued, failed = cur.fetchone(); return {"documents": docs, "queued": queued, "failed": failed}
