PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, canonical_url TEXT NOT NULL UNIQUE, domain TEXT NOT NULL DEFAULT '', title TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '', body_text TEXT NOT NULL DEFAULT '', status_code INTEGER NOT NULL DEFAULT 200, fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS documents_domain_idx ON documents (domain);
CREATE INDEX IF NOT EXISTS documents_search_idx ON documents (title, description, body_text);
CREATE TABLE IF NOT EXISTS crawl_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL UNIQUE, source_url TEXT NOT NULL DEFAULT '', domain TEXT NOT NULL DEFAULT '', priority INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, locked_at TEXT, last_error TEXT);
CREATE INDEX IF NOT EXISTS crawl_queue_ready_idx ON crawl_queue (status, next_attempt_at, priority DESC);
