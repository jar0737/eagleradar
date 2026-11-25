"""Turn place names into coordinates with the local gazetteer (FA-06). Works offline.

Geocode all place mentions in the database that have no coordinates yet:
    uv run python -m eagleradar.geo.geocoder

Try a single name:
    uv run python -m eagleradar.geo.geocoder "Bhf Südkreuz"
"""

import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import product
from math import cos, hypot, radians

import psycopg

from eagleradar.geo.gazetteer import Place, normalize, read_db

AREAS = ("locality", "district")  # most precise first
# Which place represents several that are at the same spot, e.g. a station and its street.
PRIORITY = {"landmark": 0, "station": 1, "street": 2}
# A station can be far from the middle of the street it is named after (up to 1.1 km in Berlin).
SAME_SPOT_M = 1500
MAX_INFLECTED_WORDS = 3  # limits the number of spellings tried for a long text


@dataclass(frozen=True)
class Result:
    status: str  # 'found', 'ambiguous' or 'unknown'
    place: Place | None = None  # only for 'found'
    candidates: tuple[Place, ...] = ()  # only for 'ambiguous', one per possible place


class Geocoder:
    def __init__(self, places: Iterable[Place]):
        self._index: dict[str, list[Place]] = defaultdict(list)
        for place in places:
            for key in {normalize(place.name), *place.variants}:
                self._index[key].append(place)

    def geocode(self, name: str, hints: Iterable[str] = ()) -> Result:
        """Find a place. `hints` are other place names from the same post.

        If a name fits several places and no hint decides, nothing is guessed: a wrong marker
        could send help to the wrong part of the city.
        """
        matches = self._lookup(name)
        if not matches:
            return Result("unknown")
        for kind in AREAS:  # 'Wannsee' alone means the locality, 'S Wannsee' the station
            areas = [p for p in matches if p.kind == kind]
            if areas:
                return Result("found", areas[0])
        matches = self._apply_hints(matches, hints)
        spots = _group(matches)
        if len(spots) == 1:
            return Result("found", _representative(spots[0]))
        return Result("ambiguous", candidates=tuple(_representative(spot) for spot in spots))

    def _lookup(self, name: str) -> list[Place]:
        for key in _spellings(normalize(name)):
            if key in self._index:
                return self._index[key]
        return []

    def _apply_hints(self, matches: list[Place], hints: Iterable[str]) -> list[Place]:
        """Keep the matches in a locality (or else a district) that a hint names."""
        areas = [p for hint in hints for p in self._lookup(hint) if p.kind in AREAS]
        for kind in AREAS:
            names = {p.name for p in areas if p.kind == kind}
            kept = [p for p in matches if getattr(p, kind) in names]
            if kept:
                return kept
        return matches


def _spellings(norm: str) -> Iterator[str]:
    """The name itself first, then forms it may have inside a German sentence."""
    yield norm
    short = re.sub(r" \d+ ?[a-z]?$", "", norm)  # house number: 'clayallee 12a'
    if short != norm:
        yield short
    words = short.split()
    # 'in der Argentinischen Allee', 'am Schlesischen Tor', 'an der Krummen Lanke'
    forms = [
        [word, word[:-2] + "e", word[:-2] + "es", word[:-2] + "er"]
        if len(word) > 4 and word.endswith("en")
        else [word]
        for word in words
    ]
    if sum(len(f) > 1 for f in forms) <= MAX_INFLECTED_WORDS:
        for combination in list(product(*forms))[1:]:
            yield " ".join(combination)
    # 'des Teltower Damms', 'des Alexanderplatzes'
    if short.endswith("es"):
        yield short[:-2]
    if short.endswith("s"):
        yield short[:-1]


def _distance_m(a: Place, b: Place) -> float:
    return hypot((a.lat - b.lat) * 111_200, (a.lon - b.lon) * 111_200 * cos(radians(a.lat)))


def _same_spot(a: Place, b: Place) -> bool:
    if a.kind == b.kind == "street" and a.name == b.name:
        return a.part == b.part
    return _distance_m(a, b) <= SAME_SPOT_M


def _group(places: list[Place]) -> list[list[Place]]:
    """Group matches that mean the same spot."""
    groups: list[list[Place]] = []
    for place in places:
        near = [g for g in groups if any(_same_spot(place, other) for other in g)]
        groups = [g for g in groups if g not in near] + [[place, *(p for g in near for p in g)]]
    return groups


def _representative(places: list[Place]) -> Place:
    # Of a street with several sections, the longest one.
    return min(places, key=lambda p: (PRIORITY[p.kind], -p.length_m))


def geocode_mentions(conn: psycopg.Connection) -> Counter:
    """Geocode all mentions without coordinates and store the result. The caller commits.

    Coordinates that exist already (set by hand, Nominatim, ...) are never changed. Running it
    again after an update of the gazetteer retries the ambiguous and unknown names.
    """
    geocoder = Geocoder(read_db(conn))
    rows = conn.execute(
        "SELECT m.id, m.mention_text,"
        " ARRAY(SELECT o.mention_text FROM place_mentions o"
        "       WHERE o.post_id = m.post_id AND o.id <> m.id)"
        " FROM place_mentions m WHERE m.geom IS NULL ORDER BY m.id"
    ).fetchall()
    counts: Counter = Counter()
    with conn.cursor() as cur:
        for mention_id, text, others in rows:
            result = geocoder.geocode(text, hints=others)
            counts[result.status] += 1
            if result.place:
                cur.execute(
                    "UPDATE place_mentions SET geocode_status = 'found', geocoded_by = 'gazetteer',"
                    " geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326) WHERE id = %s",
                    (result.place.lon, result.place.lat, mention_id),
                )
            else:
                cur.execute(
                    "UPDATE place_mentions SET geocode_status = %s WHERE id = %s",
                    (result.status, mention_id),
                )
    return counts


def _print_result(result: Result) -> None:
    print(result.status)
    for p in (result.place,) if result.place else result.candidates:
        print(f"  {p.name} ({p.kind}), {p.locality or p.district}: {p.lat:.5f}, {p.lon:.5f}")


def main() -> None:
    from eagleradar.db import connect

    try:
        with connect(connect_timeout=5) as conn:
            if conn.execute("SELECT count(*) FROM places").fetchone()[0] == 0:
                raise SystemExit("No places loaded: uv run python -m eagleradar.geo.gazetteer")
            if len(sys.argv) > 1:
                _print_result(Geocoder(read_db(conn)).geocode(sys.argv[1], hints=sys.argv[2:]))
            else:
                counts = geocode_mentions(conn)
                print(", ".join(f"{n} {status}" for status, n in counts.items()) or "nothing to do")
    except (psycopg.errors.UndefinedTable, psycopg.errors.UndefinedColumn):
        raise SystemExit("The database schema is outdated. Run db/schema.sql first.") from None
    except psycopg.OperationalError as exc:
        raise SystemExit(f"Cannot reach the database (docker compose up -d): {exc}") from exc


if __name__ == "__main__":
    main()
