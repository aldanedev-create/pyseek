import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import psycopg


class Database:
    def __init__(self):
        self._schema_ready = False

    @property
    def url(self):
        return os.getenv("DATABASE_URL", "").strip()

    @property
    def sqlite_mode(self):
        return not self.url or self.url.startswith("sqlite://")

    @property
    def sqlite_path(self):
        configured = self.url.removeprefix("sqlite://") if self.url.startswith("sqlite://") else ""
        return Path(configured or os.getenv("PYSEEK_SQLITE_PATH", "pyseek.local.db")).resolve()

    @contextmanager
    def connect(self):
        if self.sqlite_mode:
            path = self.sqlite_path
            path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            try:
                yield connection
                connection.commit()
            finally:
                connection.close()
            return
        with psycopg.connect(self.url, connect_timeout=8) as connection:
            yield connection

    def ensure_schema(self):
        if self._schema_ready:
            return
        from pathlib import Path
        schema_name = "sqlite_schema.sql" if self.sqlite_mode else "schema.sql"
        sql = (Path(__file__).parent / schema_name).read_text(encoding="utf-8")
        with self.connect() as connection:
            if self.sqlite_mode:
                connection.executescript(sql)
                self._schema_ready = True
                return
            with connection.cursor() as cursor:
                cursor.execute(sql)
        self._schema_ready = True


database = Database()
