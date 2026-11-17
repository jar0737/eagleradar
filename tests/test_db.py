"""Database tests (PostgreSQL + PostGIS + db/schema.sql).

Locally they are skipped when no database is running (start it with `docker compose up -d`).
In CI, EAGLERADAR_REQUIRE_DB=1 is set, so a missing database fails the build instead.
Nothing is left behind: every test rolls back its changes.
"""

import os

import psycopg
import pytest

from eagleradar.db import check, connect

REQUIRE_DB = os.getenv("EAGLERADAR_REQUIRE_DB") == "1"
PROJECT_TABLES = {"posts", "post_images", "place_mentions", "geocode_cache"}


@pytest.fixture(scope="module")
def conn():
    try:
        conn = connect(connect_timeout=5)
    except psycopg.OperationalError as exc:
        if REQUIRE_DB:
            pytest.fail(f"database required (EAGLERADAR_REQUIRE_DB=1) but not reachable: {exc}")
        pytest.skip("database not running (docker compose up -d)")
    yield conn
    conn.close()


@pytest.fixture
def tx(conn):
    """The connection, with everything a test writes rolled back afterwards."""
    yield conn
    conn.rollback()


def test_database_has_postgis(conn):
    assert "PostGIS" in check()


def test_schema_tables_exist(tx):
    rows = tx.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).fetchall()
    missing = PROJECT_TABLES - {name for (name,) in rows}
    assert not missing, f"tables missing: {sorted(missing)} - run db/schema.sql"


def test_place_mention_roundtrip(tx):
    post_id = tx.execute(
        "INSERT INTO posts (source, source_post_id, text, created_at)"
        " VALUES ('test', 'roundtrip-1', 'Stromausfall Tiergartenstr.', now()) RETURNING id"
    ).fetchone()[0]
    tx.execute(
        "INSERT INTO place_mentions (post_id, mention_text, detected_by, confidence, geom)"
        " VALUES (%s, 'Tiergartenstr.', 'regex', 0.9,"
        " ST_SetSRID(ST_MakePoint(13.35, 52.51), 4326))",
        (post_id,),
    )

    # Find mentions within 1 km of a nearby point (geography cast = distance in metres).
    lon, lat = tx.execute(
        "SELECT ST_X(geom), ST_Y(geom) FROM place_mentions"
        " WHERE post_id = %s"
        " AND ST_DWithin(geom::geography, ST_MakePoint(13.36, 52.51)::geography, 1000)",
        (post_id,),
    ).fetchone()
    assert (round(lon, 2), round(lat, 2)) == (13.35, 52.51)


def test_same_post_cannot_be_imported_twice(tx):
    insert = (
        "INSERT INTO posts (source, source_post_id, created_at) VALUES ('test', 'dup-1', now())"
    )
    tx.execute(insert)
    with pytest.raises(psycopg.errors.UniqueViolation):
        tx.execute(insert)
