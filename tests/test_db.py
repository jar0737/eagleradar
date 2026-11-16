"""Database connection test. Skipped when no database is running (e.g. in CI)."""

import psycopg
import pytest

from eagleradar.db import check


def test_database_has_postgis():
    try:
        result = check()
    except psycopg.OperationalError:
        pytest.skip("database not running (docker compose up -d)")
    assert "PostGIS" in result
