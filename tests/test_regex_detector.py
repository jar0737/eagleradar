from eagleradar.nlp.place_mention import PlaceMention
from eagleradar.nlp.regex_detector import (
    INTERSECTION_PATTERN,
    PUBLIC_TRANSPORT_PATTERN,
    STATION_PREFIX_PATTERN,
    STREET_PATTERN,
    find_regex_places,
)

# Street detection


def test_detect_street_names():
    text = "Störung auf der Skalitzer Str. und in der Potsdamer Chaussee."

    results = [match.group() for match in STREET_PATTERN.finditer(text)]

    assert "Skalitzer Str." in results
    assert "Potsdamer Chaussee" in results


# Station detection


def test_detect_station_prefixes():
    text = "Störung am Bhf Südkreuz und Bahnhof Alexanderplatz."

    results = [match.group() for match in STATION_PREFIX_PATTERN.finditer(text)]

    assert "Bhf Südkreuz" in results
    assert "Bahnhof Alexanderplatz" in results


def test_detect_public_transport_stations():
    text = "Störung bei U Alexanderplatz und S Südkreuz."

    results = [match.group() for match in PUBLIC_TRANSPORT_PATTERN.finditer(text)]

    assert "U Alexanderplatz" in results
    assert "S Südkreuz" in results


# Intersection detection


def test_detect_intersection_with_slash():
    text = "Störung an der Ecke Skalitzer Str. / Oranienstr."

    match = INTERSECTION_PATTERN.search(text)

    assert match is not None
    assert match.group("street1") == "Skalitzer Str."
    assert match.group("street2") == "Oranienstr."


def test_detect_intersection_with_und():
    text = "Kreuzung Müllerstraße und Seestraße"

    match = INTERSECTION_PATTERN.search(text)

    assert match is not None
    assert match.group("street1") == "Müllerstraße"
    assert match.group("street2") == "Seestraße"


# PlaceMention conversion


def test_find_regex_places_returns_place_mentions():
    text = "Störung am Bhf Südkreuz und auf der Skalitzer Str."

    places = find_regex_places(text)

    assert len(places) >= 2

    assert all(isinstance(place, PlaceMention) for place in places)

    assert any(place.text == "Bhf Südkreuz" for place in places)
    assert any(place.text == "Skalitzer Str." for place in places)


def test_find_regex_places_detects_intersection():
    text = "Störung an der Ecke Skalitzer Str. / Oranienstr."

    places = find_regex_places(text)

    intersections = [place for place in places if place.type == "intersection"]

    assert len(intersections) == 1

    intersection = intersections[0]

    assert intersection.text == "Skalitzer Str. / Oranienstr."
    assert intersection.normalized_name == intersection.text
    assert intersection.detected_by == ["regex"]


def test_intersection_preserves_positions():
    text = "Störung an der Ecke Skalitzer Str. / Oranienstr."

    places = find_regex_places(text)

    intersection = next(place for place in places if place.type == "intersection")

    assert text[intersection.start : intersection.end] == intersection.text


def test_find_regex_places_empty_text():
    assert find_regex_places("") == []


def test_find_regex_places_source():
    places = find_regex_places(
        "Störung am Bhf Südkreuz.",
        source="voice_to_text",
    )

    assert places[0].source == "voice_to_text"


def test_find_regex_places_preserves_all_positions():
    text = "Störung am Bhf Südkreuz."

    places = find_regex_places(text)

    station = next(place for place in places if place.text == "Bhf Südkreuz")

    assert text[station.start : station.end] == station.text


def test_street_pattern_does_not_match_normal_words():
    text = "Heute ist das Wetter schön und die Situation entspannt."

    results = [match.group() for match in STREET_PATTERN.finditer(text)]

    assert results == []


def test_station_pattern_does_not_match_normal_words():
    text = "Heute bin ich am arbeiten und danach gehe ich nach Hause."

    results = [match.group() for match in STATION_PREFIX_PATTERN.finditer(text)]

    assert results == []


def test_public_transport_pattern_does_not_match_normal_words():
    text = "Heute ist alles super und ich gehe später einkaufen."

    results = [match.group() for match in PUBLIC_TRANSPORT_PATTERN.finditer(text)]

    assert results == []


def test_intersection_pattern_does_not_match_normal_words():
    text = "An der Ecke war eine schöne Situation."

    match = INTERSECTION_PATTERN.search(text)

    assert match is None
