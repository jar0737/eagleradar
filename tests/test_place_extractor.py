from eagleradar.nlp.place_extractor import (
    extract_places,
    find_places_basic,
    find_places_basic_with_gazetteer,
    match_gazetteer,
    merge_places,
)
from eagleradar.nlp.place_mention import (
    IntersectionRelation,
    PlaceExtractionResult,
    PlaceMention,
)


def mock_gliner_empty(monkeypatch):
    """Ersetzt GLiNER durch einen Detector ohne Treffer."""

    monkeypatch.setattr(
        "eagleradar.nlp.place_extractor.find_gliner_places",
        lambda text, source: [],
    )


def create_mention(
    text,
    normalized_name,
    place_type,
    start,
    end,
    detected_by,
    confidence=0.9,
):
    return PlaceMention(
        text=text,
        normalized_name=normalized_name,
        type=place_type,
        start=start,
        end=end,
        detected_by=detected_by,
        confidence=confidence,
        source="video_description",
    )


# Gazetteer matching


def test_match_gazetteer_alias():
    place = create_mention(
        "Kotti",
        "Kotti",
        "landmark",
        0,
        5,
        ["gliner"],
    )

    results = match_gazetteer([place])

    assert len(results) == 1
    assert results[0].text == "Kotti"
    assert results[0].normalized_name == "Kottbusser Tor"
    assert results[0].type == "station"


def test_match_multiple_gazetteer_places():
    text = "Wir treffen uns am Kotti und später am Alex."

    kotti = create_mention(
        "Kotti",
        "Kotti",
        "landmark",
        text.index("Kotti"),
        text.index("Kotti") + len("Kotti"),
        ["gliner"],
    )

    alex = create_mention(
        "Alex",
        "Alex",
        "landmark",
        text.index("Alex"),
        text.index("Alex") + len("Alex"),
        ["gliner"],
    )

    results = match_gazetteer([kotti, alex])

    assert len(results) == 2
    assert results[0].normalized_name == "Kottbusser Tor"
    assert results[1].normalized_name == "Alexanderplatz"


def test_match_official_gazetteer_name():
    place = create_mention(
        "Alexanderplatz",
        "Alexanderplatz",
        "landmark",
        0,
        14,
        ["gliner"],
    )

    results = match_gazetteer([place])

    assert len(results) == 1
    assert results[0].normalized_name == "Alexanderplatz"


def test_unknown_place_remains_unchanged():
    place = create_mention(
        "Unbekannter Ort",
        "Unbekannter Ort",
        "landmark",
        0,
        15,
        ["gliner"],
    )

    results = match_gazetteer([place])

    assert len(results) == 1
    assert results[0].normalized_name == "Unbekannter Ort"


def test_match_gazetteer_saves_fuzzy_score():
    place = create_mention(
        "Alexanderplaz",
        "Alexanderplaz",
        "landmark",
        0,
        13,
        ["gliner"],
        confidence=0.75,
    )

    result = match_gazetteer([place])

    assert len(result) == 1
    assert result[0].normalized_name == "Alexanderplatz"
    assert result[0].fuzzy_score is not None
    assert result[0].fuzzy_score >= 85
    assert "rapidfuzz" in result[0].detected_by
    assert result[0].confidence == 0.75


# Basic extraction


def test_find_places_basic_combines_detectors(monkeypatch):
    text = "Treffen am Kotti und später an der Skalitzer Str."

    start = text.index("Kotti")
    end = start + len("Kotti")

    gliner_mention = create_mention(
        "Kotti",
        "Kotti",
        "landmark",
        start,
        end,
        ["gliner"],
        confidence=0.93,
    )

    monkeypatch.setattr(
        "eagleradar.nlp.place_extractor.find_gliner_places",
        lambda text, source: [gliner_mention],
    )

    results = find_places_basic_with_gazetteer(text)

    assert any(place.normalized_name == "Kottbusser Tor" for place in results)
    assert any(place.text == "Skalitzer Str." for place in results)


def test_find_places_basic_preserves_original_text(monkeypatch):
    mock_gliner_empty(monkeypatch)

    text = "Treffen am Kotti\nund an der Skalitzer Str."

    results = find_places_basic_with_gazetteer(text)

    for place in results:
        assert text[place.start : place.end] == place.text


def test_find_places_basic_sorts_results(monkeypatch):
    mock_gliner_empty(monkeypatch)

    text = "Skalitzer Str. und danach Kotti"

    results = find_places_basic_with_gazetteer(text)

    positions = [place.start for place in results]

    assert positions == sorted(positions)


def test_find_places_basic_empty_input():
    assert find_places_basic("") == []


# Merge behavior


def test_merge_identical_places():
    first = create_mention(
        "Alexanderplatz",
        "Alexanderplatz",
        "landmark",
        0,
        14,
        ["gliner"],
    )

    second = create_mention(
        "Alexanderplatz",
        "Alexanderplatz",
        "station",
        0,
        14,
        ["regex"],
    )

    results = merge_places([first, second])

    assert len(results) == 1
    assert set(results[0].detected_by) == {"gliner", "regex"}


def test_merge_overlapping_places_with_same_name():
    first = create_mention(
        "Alexanderplatz",
        "Alexanderplatz",
        "landmark",
        0,
        14,
        ["gliner"],
        0.9,
    )

    second = create_mention(
        "Alexanderplatz",
        "Alexanderplatz",
        "station",
        5,
        14,
        ["gazetteer"],
        0.95,
    )

    results = merge_places([first, second])

    assert len(results) == 1
    assert results[0].start == 0
    assert results[0].end == 14
    assert results[0].normalized_name == "Alexanderplatz"
    assert results[0].confidence == 0.95
    assert set(results[0].detected_by) == {"gliner", "gazetteer"}
    assert results[0].type == "station"


def test_overlapping_different_places_are_not_merged():
    first = create_mention(
        "Alexanderplatz",
        "Alexanderplatz",
        "station",
        0,
        14,
        ["gliner"],
    )

    second = create_mention(
        "Alexander",
        "Alexander",
        "landmark",
        0,
        9,
        ["regex"],
    )

    results = merge_places([first, second])

    assert len(results) == 2


def test_merge_empty_list():
    assert merge_places([]) == []


def test_merge_keeps_different_places_at_same_position():
    place1 = create_mention(
        "Alexanderplatz",
        "Alexanderplatz",
        "station",
        0,
        14,
        ["regex"],
    )

    place2 = create_mention(
        "Alexanderplatz",
        "Alexanderplatz Alternative",
        "landmark",
        0,
        14,
        ["gliner"],
    )

    result = merge_places([place1, place2])

    assert len(result) == 2


# Complete extraction result


def test_extract_places_returns_extraction_result(monkeypatch):
    mock_gliner_empty(monkeypatch)

    text = "An der Ecke Friedrichstraße und Leipziger Straße stehen mehrere Einsatzwagen."

    result = extract_places(text)

    assert isinstance(result, PlaceExtractionResult)
    assert len(result.places) == 2
    assert len(result.relations) == 1

    assert all(isinstance(place, PlaceMention) for place in result.places)

    assert isinstance(result.relations[0], IntersectionRelation)


def test_extract_places_preserves_intersection_positions(monkeypatch):
    mock_gliner_empty(monkeypatch)

    text = "An der Ecke Skalitzer Str. / Oranienstr."

    result = extract_places(text)

    assert len(result.relations) == 1

    relation = result.relations[0]

    assert text[relation.street1_start : relation.street1_end] == ("Skalitzer Str.")
    assert text[relation.street2_start : relation.street2_end] == ("Oranienstr.")


def test_extract_places_empty_input():
    result = extract_places("")

    assert isinstance(result, PlaceExtractionResult)
    assert result.places == []
    assert result.relations == []
