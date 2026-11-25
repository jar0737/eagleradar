"""Geocoder tests: offline, without the database and without the extras."""

import socket

import pytest

from eagleradar.geo.gazetteer import DEFAULT_CSV, Place, read_csv, station_variants
from eagleradar.geo.geocoder import Geocoder

SZ = "Steglitz-Zehlendorf"


def street(name, lat, lon, locality, district, part=0, length_m=500):
    return Place(name, "street", lat, lon, "osm", locality, district, part=part, length_m=length_m)


def station(name, lat, lon, locality="Zehlendorf", district=SZ):
    variants = tuple(station_variants(name))
    return Place(name, "station", lat, lon, "osm", locality, district, variants)


PLACES = [
    Place("Wannsee", "locality", 52.420, 13.135, "alkis", "Wannsee", SZ),
    Place("Schöneberg", "locality", 52.482, 13.352, "alkis", "Schöneberg", "Tempelhof-Schöneberg"),
    Place("Spandau", "district", 52.535, 13.200, "alkis", None, "Spandau"),
    Place("Rathaus Zehlendorf", "landmark", 52.434, 13.260, "osm", "Zehlendorf", SZ),
    station("Wannsee", 52.421, 13.179, "Wannsee"),
    station("Krumme Lanke", 52.443, 13.241),
    station("Sundgauer Straße", 52.437, 13.274),
    street("Sundgauer Straße", 52.438, 13.276, "Zehlendorf", SZ),
    station("Schlesisches Tor", 52.501, 13.442, "Kreuzberg", "Friedrichshain-Kreuzberg"),
    street("Teltower Damm", 52.421, 13.264, "Zehlendorf", SZ),
    street("Argentinische Allee", 52.446, 13.244, "Zehlendorf", SZ),
    street("Alexanderplatz", 52.521, 13.412, "Mitte", "Mitte"),
    # One street through three localities
    street("Clayallee", 52.440, 13.260, "Zehlendorf", SZ),
    street("Clayallee", 52.458, 13.272, "Dahlem", SZ, length_m=2500),
    street("Clayallee", 52.480, 13.285, "Schmargendorf", "Charlottenburg-Wilmersdorf"),
    # Two different streets
    street("Hauptstraße", 52.484, 13.352, "Schöneberg", "Tempelhof-Schöneberg", part=0),
    street("Hauptstraße", 52.530, 13.140, "Staaken", "Spandau", part=1),
]


@pytest.fixture(scope="module")
def geocoder():
    return Geocoder(PLACES)


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        ("Teltower Damm", "Teltower Damm"),
        ("TELTOWER DAMM", "Teltower Damm"),
        ("Teltower Damm 12a", "Teltower Damm"),
        ("Teltower Damms", "Teltower Damm"),
        ("Alexanderplatzes", "Alexanderplatz"),
        ("Sundgauer Str.", "Sundgauer Straße"),
        ("Argentinischen Allee", "Argentinische Allee"),
        ("Krummen Lanke", "Krumme Lanke"),
        ("Schlesischen Tor", "Schlesisches Tor"),
        ("U Krumme Lanke", "Krumme Lanke"),
        ("U-Bhf. Krumme Lanke", "Krumme Lanke"),
        ("Rathaus Zehlendorf", "Rathaus Zehlendorf"),
    ],
)
def test_spellings_are_found(geocoder, written, expected):
    result = geocoder.geocode(written)
    assert result.status == "found"
    assert result.place.name == expected


@pytest.mark.parametrize(
    "written", ["Kiosk am Eck", "", "   ", "???", "12", "王秀英", "laufen " * 40]
)
def test_unknown_places_do_not_crash(geocoder, written):
    result = geocoder.geocode(written)
    assert (result.status, result.place, result.candidates) == ("unknown", None, ())


def test_area_name_means_the_area_and_s_means_the_station(geocoder):
    assert geocoder.geocode("Wannsee").place.kind == "locality"
    assert geocoder.geocode("S Wannsee").place.kind == "station"
    assert geocoder.geocode("Spandau").place.kind == "district"


def test_station_and_street_at_the_same_spot_are_one_place(geocoder):
    assert geocoder.geocode("Sundgauer Straße").place.kind == "station"


def test_station_far_from_the_middle_of_its_street_is_one_place():
    damm = street("Hohenzollerndamm", 52.480, 13.300, "Wilmersdorf", "Charlottenburg-Wilmersdorf")
    stop = station("Hohenzollerndamm", 52.488, 13.300)  # 890 m away
    assert Geocoder([damm, stop]).geocode("Hohenzollerndamm").place == stop


def test_continuous_street_is_one_place(geocoder):
    result = geocoder.geocode("Clayallee")
    assert result.status == "found"
    assert result.place.locality == "Dahlem"  # the longest section


def test_different_streets_are_not_guessed(geocoder):
    result = geocoder.geocode("Hauptstraße")
    assert result.status == "ambiguous"
    assert result.place is None
    assert {p.locality for p in result.candidates} == {"Schöneberg", "Staaken"}


@pytest.mark.parametrize(
    ("hints", "expected"),
    [
        (["Schöneberg"], "Schöneberg"),  # locality
        (["Spandau"], "Staaken"),  # district
        (["Kiosk am Eck", "Spandau"], "Staaken"),
    ],
)
def test_a_hint_from_the_post_decides(geocoder, hints, expected):
    assert geocoder.geocode("Hauptstr.", hints).place.locality == expected


@pytest.mark.parametrize("hints", [["Wannsee"], ["Teltower Damm"], ["Spandau", "Schöneberg"]])
def test_a_hint_that_does_not_fit_decides_nothing_wrong(geocoder, hints):
    result = geocoder.geocode("Hauptstraße", hints)
    if hints == ["Spandau", "Schöneberg"]:
        assert result.place.locality == "Schöneberg"  # the locality is more precise
    else:
        assert result.status == "ambiguous"


def test_a_hint_narrows_a_long_street(geocoder):
    assert geocoder.geocode("Clayallee", ["Spandau"]).place.locality == "Dahlem"


@pytest.mark.skipif(not DEFAULT_CSV.exists(), reason="run scripts/build_gazetteer.py first")
def test_committed_list_works_without_internet(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("the geocoder must not use the network")

    monkeypatch.setattr(socket, "socket", no_network)
    geocoder = Geocoder(read_csv())
    for written, locality in [
        ("Teltower Damm", "Zehlendorf"),
        ("U Krumme Lanke", "Zehlendorf"),
        ("Argentinischen Allee", "Zehlendorf"),
        ("Rathaus Zehlendorf", "Zehlendorf"),
        ("Bhf Südkreuz", "Schöneberg"),
        ("Hauptbahnhof", "Moabit"),
    ]:
        result = geocoder.geocode(written)
        assert (result.status, result.place and result.place.locality) == ("found", locality)
    assert geocoder.geocode("Tiergartenstr.", ["Tiergarten"]).place.locality == "Tiergarten"
    assert geocoder.geocode("Hauptstraße").status == "ambiguous"
    assert geocoder.geocode("Kiosk am Eck").status == "unknown"
