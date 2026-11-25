"""Gazetteer: local list of places in Berlin.

Kinds: street, station, landmark (town halls, hospitals, police and fire stations), locality
and district.

The list is data/sample/gazetteer.csv. It is built by scripts/build_gazetteer.py and works
without an internet connection.

Load it into the database (replaces the current content of the `places` table):
    uv run python -m eagleradar.geo.gazetteer
"""

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import psycopg

DEFAULT_CSV = Path(__file__).parents[3] / "data" / "sample" / "gazetteer.csv"
COLUMNS = [
    "name",
    "variants",
    "kind",
    "part",
    "length_m",
    "locality",
    "district",
    "lat",
    "lon",
    "source",
]
VARIANT_SEPARATOR = "|"

_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue"})
_STATION_PREFIXES = ("u", "s", "s u", "u s", "bahnhof", "u bahnhof", "s bahnhof")


@dataclass(frozen=True)
class Place:
    name: str
    kind: str  # 'street', 'station', 'landmark', 'locality' or 'district'
    lat: float
    lon: float
    source: str  # 'osm' or 'alkis'
    locality: str | None = None
    district: str | None = None
    variants: tuple[str, ...] = ()  # already normalized
    part: int = 0  # rows with the same name and part are one continuous street
    length_m: int = 0  # length of the street in this locality


def normalize(name: str) -> str:
    """Spelling used for lookup. Use it for the list AND for the names found in posts.

    >>> normalize("Tiergartenstr.") == normalize("Tiergartenstraße")
    True
    """
    # NFC first: an umlaut can also be stored as a letter plus a combining mark.
    text = unicodedata.normalize("NFC", name).casefold().translate(_UMLAUTS)
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = re.sub(r"\bhbf\b", "hauptbahnhof", text)
    text = re.sub(r"\bbhf\b", "bahnhof", text)
    text = re.sub(r"str\b", "strasse", text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def station_variants(name: str) -> list[str]:
    """Normalized names people use for a station, e.g. 'u krumme lanke'."""
    norm = normalize(name)
    return [f"{prefix} {norm}" for prefix in _STATION_PREFIXES]


def read_csv(path: Path = DEFAULT_CSV) -> list[Place]:
    """Read the place list. Raises ValueError with the line number if a row is unusable."""
    places = []
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"{path.name}: expected columns {COLUMNS}, got {reader.fieldnames}")
        for row in reader:
            try:
                lat, lon = float(row["lat"]), float(row["lon"])
            except (TypeError, ValueError):
                raise ValueError(f"{path.name}, line {reader.line_num}: bad coordinates") from None
            if not (52 < lat < 53 and 13 < lon < 14):  # also catches swapped lat/lon
                raise ValueError(f"{path.name}, line {reader.line_num}: not in Berlin")
            places.append(
                Place(
                    name=row["name"],
                    kind=row["kind"],
                    lat=lat,
                    lon=lon,
                    source=row["source"],
                    locality=row["locality"] or None,
                    district=row["district"] or None,
                    variants=tuple(v for v in row["variants"].split(VARIANT_SEPARATOR) if v),
                    part=int(row["part"]),
                    length_m=int(row["length_m"]),
                )
            )
    return places


def write_csv(places: list[Place], path: Path) -> None:
    """Write the place list, sorted so that a rebuild gives a readable Git diff."""
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(COLUMNS)
        for p in sorted(places, key=lambda p: (p.kind, p.name, p.locality or "")):
            writer.writerow(
                [
                    p.name,
                    VARIANT_SEPARATOR.join(p.variants),
                    p.kind,
                    p.part,
                    p.length_m,
                    p.locality or "",
                    p.district or "",
                    f"{p.lat:.5f}",
                    f"{p.lon:.5f}",
                    p.source,
                ]
            )


def load(conn: psycopg.Connection, places: list[Place]) -> int:
    """Replace the content of the `places` table. The caller commits."""
    rows = [
        (p.name, normalize(p.name), list(p.variants), p.kind, p.part, p.length_m)
        + (p.locality, p.district, p.lon, p.lat, p.source)
        for p in places
    ]
    with conn.cursor() as cur:
        cur.execute("DELETE FROM places")
        cur.executemany(
            "INSERT INTO places"
            " (name, name_norm, variants, kind, part, length_m,"
            "  locality, district, geom, source)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s,"
            "  ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)",
            rows,
        )
    return len(rows)


def read_db(conn: psycopg.Connection) -> list[Place]:
    """Read the place list from the `places` table."""
    rows = conn.execute(
        "SELECT name, kind, ST_Y(geom), ST_X(geom), source, locality, district, variants,"
        " part, length_m FROM places ORDER BY id"
    )
    return [Place(*row[:7], tuple(row[7]), *row[8:]) for row in rows]


def main() -> None:
    from eagleradar.db import connect

    if not DEFAULT_CSV.exists():
        raise SystemExit(f"{DEFAULT_CSV} not found. Build it with scripts/build_gazetteer.py")
    places = read_csv()
    try:
        with connect(connect_timeout=5) as conn:
            count = load(conn, places)
    except psycopg.errors.UndefinedTable:
        raise SystemExit("Table `places` is missing. Run db/schema.sql first.") from None
    except psycopg.OperationalError as exc:
        raise SystemExit(f"Cannot reach the database (docker compose up -d): {exc}") from exc
    print(f"{count} places loaded")


if __name__ == "__main__":
    main()
