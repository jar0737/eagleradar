from unittest.mock import patch

from eagleradar.nlp.gliner_detector import find_gliner_places


def test_find_gliner_places_returns_place_mentions():
    text = "Ich gehe zum Alexanderplatz."

    fake_entities = [
        {
            "text": "Alexanderplatz",
            "label": "landmark",
            "start": 13,
            "end": 27,
            "score": 0.94,
        }
    ]

    with patch("eagleradar.nlp.gliner_detector.load_model") as mock_load:
        mock_load.return_value.predict_entities.return_value = fake_entities

        results = find_gliner_places(text)

    assert len(results) == 1
    assert results[0].text == "Alexanderplatz"
    assert results[0].normalized_name == "Alexanderplatz"
    assert results[0].type == "landmark"
    assert results[0].detected_by == ["gliner"]
    assert results[0].confidence == 0.94


def test_find_gliner_places_empty_text():
    assert find_gliner_places("") == []


def test_find_gliner_places_preserves_positions():
    text = "Treffen am Alexanderplatz."

    fake_entities = [
        {
            "text": "Alexanderplatz",
            "label": "landmark",
            "start": 11,
            "end": 25,
            "score": 0.94,
        }
    ]

    with patch("eagleradar.nlp.gliner_detector.load_model") as mock_load:
        mock_load.return_value.predict_entities.return_value = fake_entities

        results = find_gliner_places(text)

    assert text[results[0].start : results[0].end] == "Alexanderplatz"


def test_find_gliner_places_uses_source():
    text = "Ich gehe zum Alexanderplatz."

    fake_entities = [
        {
            "text": "Alexanderplatz",
            "label": "landmark",
            "start": 13,
            "end": 27,
            "score": 0.94,
        }
    ]

    with patch("eagleradar.nlp.gliner_detector.load_model") as mock_load:
        mock_load.return_value.predict_entities.return_value = fake_entities

        results = find_gliner_places(text, source="ocr")

    assert results[0].source == "ocr"
