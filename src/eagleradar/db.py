"""Database connection (PostgreSQL + PostGIS).

The connection string comes from DATABASE_URL in .env (see .env.example).
Start the database first with `docker compose up -d`.

Usage:
    from eagleradar.db import connect

    with connect() as conn:
        rows = conn.execute("SELECT id, text FROM posts LIMIT 5").fetchall()

Check the connection from the terminal:
    uv run python -m eagleradar.db
"""

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = "postgresql://eagleradar:eagleradar@localhost:5432/eagleradar"


def database_url() -> str:
    """Connection string from DATABASE_URL, or the docker compose default."""
    return os.getenv("DATABASE_URL", DEFAULT_URL)


def connect(**kwargs) -> psycopg.Connection:
    """Open a new connection. Use it in a `with` block: it commits on success,
    rolls back on error and closes at the end."""
    return psycopg.connect(database_url(), **kwargs)


def check() -> str:
    """Return the PostgreSQL and PostGIS versions; raises if the database is unreachable."""
    with connect(connect_timeout=5) as conn:
        pg = conn.execute("SHOW server_version").fetchone()[0]
        postgis = conn.execute("SELECT postgis_lib_version()").fetchone()[0]
        tables = conn.execute(
            "SELECT count(*) FROM information_schema.tables"
            " WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            " AND table_name <> 'spatial_ref_sys'"
        ).fetchone()[0]
    return f"PostgreSQL {pg}, PostGIS {postgis}, {tables} project tables"


if __name__ == "__main__":
    try:
        print(f"Connected: {check()}")
    except psycopg.OperationalError as exc:
        raise SystemExit(
            f"Cannot reach the database at {database_url()}\n"
            "Is it running? Start it with: docker compose up -d\n"
            f"Details: {exc}"
        ) from exc
