# Deploy PySeek to Vercel + Neon

1. For local development, leave `DATABASE_URL` empty and PySeek uses `pyseek.local.db` with SQLite. For Vercel, create a Neon PostgreSQL database and copy its pooled `DATABASE_URL`.
2. From `pyseek`, install dependencies and set the URL: `pip install -r requirements.txt` and `$env:DATABASE_URL='postgresql://...'`.
3. Initialize the schema once: `python -c "from database.connection import database; database.ensure_schema(); print('schema ready')"`.
4. Seed trusted public sites: `python scripts/seed.py https://example.com`.
5. Run one crawl batch locally with `python scripts/crawl_once.py`.
6. Build the `.vel` frontend with `python build.py`, then verify `public/static/js/App.js` exists. Vercel's `/assets/*` rewrite maps that published directory to the browser URL.
7. Import the project into Vercel with the project root set to `pyseek`.
8. Add `DATABASE_URL`, `CRON_SECRET`, `CRAWLER_USER_AGENT`, `CRAWL_BATCH_SIZE`, and `CRAWL_MAX_BYTES` as Vercel environment variables. Never expose `DATABASE_URL` to browser variables.
9. Deploy and call `/api/health`. Use the secret in `Authorization: Bearer ...` when testing `/api/cron/crawl`.

Vercel functions have bounded execution time, so the crawler is intentionally a batch worker. It does not pretend a serverless request can run forever. The cron schedule in `vercel.json` is daily-compatible with the lowest Vercel plan; use a paid plan or an external scheduler for more frequent crawling.
