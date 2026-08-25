# API

- `GET /api/health` — deployment health and whether `DATABASE_URL` is configured.
- `GET /api/search?q=python&domain=example.com` — full-text search response.
- `GET /api/suggest?q=py` — title suggestions.
- `GET /api/stats` — indexed, queued, and failed counts.
- `POST /api/internal/seed` — secret-protected JSON body `{ "urls": ["https://example.com"] }`.
- `GET /api/cron/crawl` — secret-protected bounded crawler batch.

All user-provided URLs are limited to HTTP(S), reject credentials, remove fragments, and reject local/private IP targets. The crawler checks `robots.txt`, restricts response size, accepts HTML only, and discovers same-origin links.
