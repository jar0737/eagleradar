import pytest
from pydantic import ValidationError

from eagleradar.nlp.place_mention import PlaceMention


def test_place_mention_creation():
    place = PlaceMention(
        text="Skalitzer Str.",
        normalized_name="Skalitzer Straße",
        type="street",
        start=20,
        end=34,
        detected_by=["regex"],
        confidence=0.95,
        source="video_description",
    )

    assert place.text == "Skalitzer Str."
    assert place.normalized_name == "Skalitzer Straße"
    assert place.type == "street"
    assert place.source == "video_description"


def test_invalid_confidence():
    with pytest.raises(ValidationError):
        PlaceMention(
            text="Kreuzberg",
            normalized_name="Kreuzberg",
            type="district",
            start=0,
            end=9,
            detected_by=["regex"],
            confidence=1.5,
            source="voice_to_text",
        )


def test_invalid_positions():
    with pytest.raises(ValidationError):
        PlaceMention(
            text="Kreuzberg",
            normalized_name="Kreuzberg",
            type="district",
            start=10,
            end=5,
            detected_by=["regex"],
            confidence=0.9,
            source="hashtag_names",
        )


def test_invalid_source():
    with pytest.raises(ValidationError):
        PlaceMention(
            text="Kreuzberg",
            normalized_name="Kreuzberg",
            type="district",
            start=0,
            end=9,
            detected_by=["regex"],
            confidence=0.9,
            source="unknown",
        )
