# PySeek

PySeek is a small, real search engine built to demonstrate Teloce-Py `.vel` components and the Flaxon Python framework. Vercel hosts the application and scheduled crawl API; Neon PostgreSQL stores the crawl queue and searchable index.

## Live website

Use the deployed search engine here: **[https://pyseek.vercel.app](https://pyseek.vercel.app)**

The main search bar searches PySeek’s indexed pages. The **Search beyond the PySeek index** panel opens Google web results in a new tab.

## What it proves

PySeek is a working reference application for Teloce-Py and Flaxon:

- eight `.vel` files are compiled with imports into a browser application;
- Flaxon serves the HTML shell and JSON API;
- Neon PostgreSQL provides a durable full-text index and crawl queue;
- a real crawler downloads HTML, checks robots.txt, parses pages, deduplicates same-origin links, and retries failures;
- IndexedDB keeps browser-local history without requiring accounts;
- Vercel Cron runs short, bounded crawl batches and the app is installable as a PWA.

It is intentionally a focused project, not a claim to index the entire public web. A production deployment must seed domains responsibly, obey their policies, monitor database usage, and provide a security contact.

PySeek can optionally add live web results through the Google Custom Search JSON API. Set `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_ID` only on the server; the local index still works when these variables are absent. See `docs/deployment.md` for configuration and quota notes.

## Run

```powershell
cd pyseek
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python build.py
flaxon run app:app --reload
```

Local development uses SQLite automatically when `DATABASE_URL` is empty. Vercel uses Neon PostgreSQL when `DATABASE_URL` is a `postgresql://` connection string. See `docs/deployment.md` and `docs/architecture.md`.

## First real crawl

```powershell
$env:DATABASE_URL = "postgresql://..."
python -c "from database.connection import database; database.ensure_schema(); print('schema ready')"
python scripts/seed.py https://example.com
python scripts/crawl_once.py
```

The public seed and cron endpoints require `CRON_SECRET` outside debug mode. Search results are shared in Neon; history is local to each browser and never needs a user account.
