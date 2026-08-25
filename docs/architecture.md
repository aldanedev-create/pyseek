# PySeek architecture

PySeek is intentionally small, but it is a real indexed crawler rather than a static search mock.

```text
browser (.vel components)
  ├─ IndexedDB: local history and saved items
  └─ Flaxon API on Vercel
       ├─ /api/search -> PostgreSQL full-text index
       ├─ /api/internal/seed -> validated crawl queue
       └─ /api/cron/crawl -> bounded worker invocation
              └─ robots.txt -> downloader -> HTML parser -> Neon
```

The frontend source is `static/js/**/*.vel`. `App.vel` imports `SearchShell.vel`, which imports the search bar, results, result card, history, and crawl status components. The compiler produces browser JavaScript under the published `public/static/js/`; the only handwritten browser JavaScript is the small IndexedDB adapter and service worker.

Neon stores durable documents and queue state in production. Local development uses the same repository API over SQLite, so developers can build and test without a database server; SQLite uses bounded `LIKE` matching locally, while Neon uses PostgreSQL `tsvector`/`websearch_to_tsquery` ranking. Browser IndexedDB is deliberately not used for the shared index: it is private to one user’s browser and cannot power a public search engine.
