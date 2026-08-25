# Development loop

```powershell
cd pyseek
pip install -r requirements.txt
$env:FLAXON_DEBUG='true'
$env:DATABASE_URL='postgresql://...'
python build.py
flaxon run app:app --reload
```

Run `pytest` from this directory. The parser, URL safety, ranking, and `.vel` build should be tested before deployment. A missing Neon URL is expected for frontend-only work; search and crawling return a clear service-unavailable response until it is configured.

For local development, SQLite is the default and requires no server: `python -c "from database.connection import database; database.ensure_schema()"`. To test PostgreSQL parity, use `docker compose up --build`; Neon uses the same PostgreSQL schema in Vercel.
