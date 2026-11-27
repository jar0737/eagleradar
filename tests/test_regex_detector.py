from eagleradar.nlp.place_mention import (
    IntersectionRelation,
    PlaceMention,
)
from eagleradar.nlp.regex_detector import (
    PUBLIC_TRANSPORT_PATTERN,
    STATION_PREFIX_PATTERN,
    STREET_PATTERN,
    find_regex_places,
    find_regex_relations,
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
    text = "Störung bei U-Bahn Alexanderplatz und S-Bahn Südkreuz."

    results = [match.group() for match in PUBLIC_TRANSPORT_PATTERN.finditer(text)]

    assert "U-Bahn Alexanderplatz" in results
    assert "S-Bahn Südkreuz" in results


# PlaceMention conversion


def test_find_regex_places_returns_place_mentions():
    text = "Störung am Bhf Südkreuz und auf der Skalitzer Str."

    places = find_regex_places(text)

    assert len(places) >= 2
    assert all(isinstance(place, PlaceMention) for place in places)

    assert any(place.text == "Bhf Südkreuz" for place in places)
    assert any(place.text == "Skalitzer Str." for place in places)


def test_find_regex_places_does_not_create_intersection_place():
    text = "Störung an der Ecke Skalitzer Str. / Oranienstr."

    places = find_regex_places(text)

    assert all(place.type != "intersection" for place in places)
    assert any(place.text == "Skalitzer Str." for place in places)
    assert any(place.text == "Oranienstr." for place in places)


# Intersection relations


def test_detect_intersection_with_slash():
    text = "Störung an der Ecke Skalitzer Str. / Oranienstr."

    places = find_regex_places(text)
    relations = find_regex_relations(text, places)

    assert len(relations) == 1

    relation = relations[0]

    assert isinstance(relation, IntersectionRelation)
    assert relation.street1 == "Skalitzer Str."
    assert relation.street2 == "Oranienstr."
    assert relation.connector == "/"


def test_detect_intersection_with_und():
    text = "Kreuzung Müllerstraße und Seestraße"

    places = find_regex_places(text)
    relations = find_regex_relations(text, places)

    assert len(relations) == 1

    relation = relations[0]

    assert relation.street1 == "Müllerstraße"
    assert relation.street2 == "Seestraße"
    assert relation.connector == "und"


def test_intersection_preserves_positions():
    text = "Störung an der Ecke Skalitzer Str. / Oranienstr."

    places = find_regex_places(text)
    relations = find_regex_relations(text, places)

    assert len(relations) == 1

    relation = relations[0]

    assert text[relation.street1_start : relation.street1_end] == "Skalitzer Str."
    assert text[relation.street2_start : relation.street2_end] == "Oranienstr."
    assert text[relation.start : relation.end] == ("Skalitzer Str. / Oranienstr.")


def test_no_intersection_without_context_and_und():
    text = "Ich kenne die Müllerstraße und die Seestraße."

    places = find_regex_places(text)
    relations = find_regex_relations(text, places)

    assert relations == []


def test_no_intersection_for_unrelated_sentence():
    text = "An der Ecke war eine schöne Situation."

    places = find_regex_places(text)
    relations = find_regex_relations(text, places)

    assert relations == []


# Empty input and source


def test_find_regex_places_empty_text():
    assert find_regex_places("") == []


def test_find_regex_places_source():
    places = find_regex_places(
        "Störung am Bhf Südkreuz.",
        source="voice_to_text",
    )

    assert places[0].source == "voice_to_text"


# Position preservation


def test_find_regex_places_preserves_all_positions():
    text = "Störung am Bhf Südkreuz."

    places = find_regex_places(text)

    station = next(place for place in places if place.text == "Bhf Südkreuz")

    assert text[station.start : station.end] == station.text


# False positive prevention


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
