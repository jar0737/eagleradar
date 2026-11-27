"""Gazetteer tests: offline, without the database and without the extras."""

import pytest

from eagleradar.geo.gazetteer import (
    DEFAULT_CSV,
    Place,
    normalize,
    read_csv,
    station_variants,
    write_csv,
)

DAMM = Place("Teltower Damm", "street", 52.43, 13.26, "osm", "Zehlendorf", "Steglitz-Zehlendorf")
LANKE = Place(
    "Krumme Lanke", "station", 52.443, 13.241, "osm", "Zehlendorf", variants=("u krumme lanke",)
)


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        ("Tiergartenstr.", "tiergartenstrasse"),
        ("Tiergartenstraße", "tiergartenstrasse"),
        ("Berliner Str", "berliner strasse"),
        ("Bhf Südkreuz", "bahnhof suedkreuz"),
        ("U-Bhf. Krumme Lanke", "u bahnhof krumme lanke"),
        ("Berlin Hbf", "berlin hauptbahnhof"),
        ("S+U Rathaus Steglitz", "s u rathaus steglitz"),
        ("Straße des 17. Juni", "strasse des 17 juni"),
        ("Südkreuz", "suedkreuz"),  # u + combining diaeresis
        ("???", ""),
    ],
)
def test_normalize(written, expected):
    assert normalize(written) == expected


def test_station_variants_match_what_people_write():
    variants = station_variants("Rathaus Steglitz")
    for written in ("U Rathaus Steglitz", "S+U Rathaus Steglitz", "S-Bhf Rathaus Steglitz"):
        assert normalize(written) in variants


def test_csv_roundtrip(tmp_path):
    path = tmp_path / "places.csv"
    write_csv([DAMM, LANKE], path)
    assert read_csv(path) == [LANKE, DAMM]  # sorted by kind


def test_swapped_coordinates_are_rejected(tmp_path):
    path = tmp_path / "places.csv"
    write_csv([Place("Teltower Damm", "street", 13.26, 52.43, "osm")], path)
    with pytest.raises(ValueError, match="line 2: not in Berlin"):
        read_csv(path)


def test_unreadable_coordinates_are_rejected(tmp_path):
    path = tmp_path / "places.csv"
    write_csv([DAMM], path)
    path.write_text(path.read_text(encoding="utf-8").replace("52.43000", "n/a"), encoding="utf-8")
    with pytest.raises(ValueError, match="line 2: bad coordinates"):
        read_csv(path)


def test_wrong_columns_are_rejected(tmp_path):
    path = tmp_path / "places.csv"
    path.write_text("name,lat\nTeltower Damm,52.43\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected columns"):
        read_csv(path)


@pytest.mark.skipif(not DEFAULT_CSV.exists(), reason="run scripts/build_gazetteer.py first")
def test_committed_list_contains_the_known_places():
    places = read_csv()
    kinds = [p.kind for p in places]
    assert kinds.count("district") == 12
    assert kinds.count("locality") > 90
    assert kinds.count("station") > 250
    assert kinds.count("landmark") > 100
    assert kinds.count("street") > 10_000

    def find(written: str, kind: str) -> list[Place]:
        norm = normalize(written)
        return [p for p in places if p.kind == kind and norm in (normalize(p.name), *p.variants)]

    assert "Zehlendorf" in {p.locality for p in find("Teltower Damm", "street")}
    for written in ("U Krumme Lanke", "S Wannsee", "Bhf Südkreuz", "S+U Rathaus Steglitz"):
        assert len(find(written, "station")) == 1, written
    assert len(find("Hauptstr.", "street")) > 1  # ambiguous on purpose
    assert len(find("Rathaus Zehlendorf", "landmark")) == 1
    assert len({p.part for p in find("Clayallee", "street")}) == 1  # one street, 4 localities
    (main_station,) = find("Hauptbahnhof", "station")  # not the park railway in Wuhlheide
    assert main_station.locality == "Moabit"
