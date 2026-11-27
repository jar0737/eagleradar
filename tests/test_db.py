"""Database tests (PostgreSQL + PostGIS + db/schema.sql).

Locally they are skipped when no database is running (start it with `docker compose up -d`).
In CI, EAGLERADAR_REQUIRE_DB=1 is set, so a missing database fails the build instead.
Nothing is left behind: every test rolls back its changes.
"""

import os

import psycopg
import pytest

from eagleradar.db import check, connect
from eagleradar.geo.gazetteer import Place, load, read_db
from eagleradar.geo.geocoder import geocode_mentions

REQUIRE_DB = os.getenv("EAGLERADAR_REQUIRE_DB") == "1"
PROJECT_TABLES = {"posts", "post_images", "place_mentions", "geocode_cache", "places"}


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


def test_gazetteer_load_replaces_the_list(tx):
    damm = Place(
        "Teltower Damm", "street", 52.43, 13.26, "osm", "Zehlendorf", "Steglitz-Zehlendorf"
    )
    lanke = Place("Krumme Lanke", "station", 52.44, 13.24, "osm", variants=("u krumme lanke",))
    assert load(tx, [damm]) == 1
    assert load(tx, [damm, lanke]) == 2  # loading again does not duplicate
    assert tx.execute("SELECT count(*) FROM places").fetchone()[0] == 2

    row = tx.execute(
        "SELECT name, ST_Y(geom), ST_X(geom) FROM places WHERE 'u krumme lanke' = ANY (variants)"
    ).fetchone()
    assert row == ("Krumme Lanke", 52.44, 13.24)
    assert tx.execute("SELECT name FROM places WHERE name_norm = 'teltower damm'").fetchall() == [
        ("Teltower Damm",)
    ]


def test_same_place_cannot_be_stored_twice(tx):
    district = Place("Mitte", "district", 52.52, 13.37, "alkis", None, "Mitte")
    with pytest.raises(psycopg.errors.UniqueViolation):
        load(tx, [district, district])


DAMM = Place("Teltower Damm", "street", 52.43, 13.26, "osm", "Zehlendorf", "Steglitz-Zehlendorf")
MAIN_A = Place("Hauptstraße", "street", 52.48, 13.35, "osm", "Schöneberg", "Tempelhof-Schöneberg")
MAIN_B = Place("Hauptstraße", "street", 52.53, 13.14, "osm", "Staaken", "Spandau", part=1)
STAAKEN = Place("Staaken", "locality", 52.53, 13.14, "alkis", "Staaken", "Spandau")


def test_gazetteer_survives_the_database(tx):
    places = [DAMM, MAIN_A, MAIN_B, STAAKEN]
    load(tx, places)
    assert read_db(tx) == places


def add_post(tx, post_id, *mentions):
    pk = tx.execute(
        "INSERT INTO posts (source, source_post_id, created_at)"
        " VALUES ('test-geo', %s, now()) RETURNING id",
        (post_id,),
    ).fetchone()[0]
    for text in mentions:
        tx.execute(
            "INSERT INTO place_mentions (post_id, mention_text, detected_by)"
            " VALUES (%s, %s, 'test')",
            (pk, text),
        )
    return pk


def mentions_of(tx, pk):
    return tx.execute(
        "SELECT mention_text, geocode_status, geocoded_by, ST_Y(geom), ST_X(geom)"
        " FROM place_mentions WHERE post_id = %s ORDER BY id",
        (pk,),
    ).fetchall()


def test_mentions_are_geocoded_and_posts_without_place_are_listed(tx):
    load(tx, [DAMM, MAIN_A, MAIN_B, STAAKEN])
    found = add_post(tx, "found", "Teltower Damm 5", "Kiosk am Eck")
    hint = add_post(tx, "hint", "Hauptstr.", "Staaken")
    ambiguous = add_post(tx, "ambiguous", "Hauptstraße")
    unknown = add_post(tx, "unknown", "Kiosk am Eck")
    none = add_post(tx, "none")

    def without_place():
        rows = tx.execute("SELECT post_id, reason FROM posts_without_place").fetchall()
        return {k: v for k, v in rows if k in (found, hint, ambiguous, unknown, none)}

    assert without_place()[found] == "pending"
    geocode_mentions(tx)

    assert mentions_of(tx, found) == [
        ("Teltower Damm 5", "found", "gazetteer", 52.43, 13.26),
        ("Kiosk am Eck", "unknown", None, None, None),
    ]
    assert mentions_of(tx, hint)[0] == ("Hauptstr.", "found", "gazetteer", 52.53, 13.14)
    assert mentions_of(tx, ambiguous) == [("Hauptstraße", "ambiguous", None, None, None)]
    assert without_place() == {ambiguous: "ambiguous", unknown: "unknown", none: "no_mention"}


def test_existing_coordinates_are_kept_and_unknown_names_are_retried(tx):
    load(tx, [STAAKEN])
    pk = add_post(tx, "keep", "Staaken", "Teltower Damm")
    tx.execute(
        "UPDATE place_mentions SET geom = ST_SetSRID(ST_MakePoint(13.5, 52.5), 4326),"
        " geocoded_by = 'manual' WHERE post_id = %s AND mention_text = 'Staaken'",
        (pk,),
    )
    geocode_mentions(tx)
    assert mentions_of(tx, pk)[0] == ("Staaken", None, "manual", 52.5, 13.5)
    assert mentions_of(tx, pk)[1][1] == "unknown"

    load(tx, [STAAKEN, DAMM])
    geocode_mentions(tx)
    assert mentions_of(tx, pk)[0][2] == "manual"
    assert mentions_of(tx, pk)[1][1] == "found"
