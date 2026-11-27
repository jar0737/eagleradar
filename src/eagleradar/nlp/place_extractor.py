from eagleradar.nlp.gazetteer import (
    find_fuzzy_match,
    find_gazetteer_match,
)
from eagleradar.nlp.gliner_detector import find_gliner_places
from eagleradar.nlp.place_mention import (
    PlaceExtractionResult,
    PlaceMention,
)
from eagleradar.nlp.regex_detector import (
    find_regex_places,
    find_regex_relations,
)


def find_places_basic(
    text: str,
    source: str = "video_description",
) -> list[PlaceMention]:
    """Führt die grundlegende Ortsnamenerkennung durch."""

    if not text or not text.strip():
        return []

    regex_places = find_regex_places(text, source)
    gliner_places = find_gliner_places(text, source)

    candidates = regex_places + gliner_places

    return merge_places(candidates)


def match_gazetteer(
    places: list[PlaceMention],
) -> list[PlaceMention]:
    """Gleicht erkannte Ortsangaben mit dem Gazetteer ab."""

    matched_places = []

    for place in places:
        exact_match = find_gazetteer_match(place.text)

        if exact_match:
            place.normalized_name = exact_match.official_name
            place.type = exact_match.type

            if "gazetteer" not in place.detected_by:
                place.detected_by.append("gazetteer")

            matched_places.append(place)
            continue

        fuzzy_match = find_fuzzy_match(place.text)

        if fuzzy_match:
            entry, score = fuzzy_match

            place.normalized_name = entry.official_name
            place.type = entry.type
            place.fuzzy_score = score

            if "rapidfuzz" not in place.detected_by:
                place.detected_by.append("rapidfuzz")

        matched_places.append(place)

    return matched_places


def merge_places(
    places: list[PlaceMention],
) -> list[PlaceMention]:
    """Führt überlappende Treffer desselben Ortes zusammen."""

    merged = []

    for place in sorted(
        places,
        key=lambda p: (p.start, p.end),
    ):
        matching_place = None

        for existing in merged:
            same_name = existing.normalized_name.casefold() == place.normalized_name.casefold()

            overlaps = existing.start < place.end and place.start < existing.end

            if same_name and overlaps:
                matching_place = existing
                break

        if matching_place is None:
            merged.append(place)
            continue

        existing = matching_place

        # Detektoren zusammenführen
        for detector in place.detected_by:
            if detector not in existing.detected_by:
                existing.detected_by.append(detector)

        # Confidence des zuverlässigeren Treffers übernehmen
        if place.confidence > existing.confidence:
            existing.confidence = place.confidence
            existing.type = place.type

        # Positionen vereinigen
        existing.start = min(existing.start, place.start)
        existing.end = max(existing.end, place.end)

        # Fuzzy Score übernehmen, falls vorhanden
        if place.fuzzy_score is not None and (
            existing.fuzzy_score is None or place.fuzzy_score > existing.fuzzy_score
        ):
            existing.fuzzy_score = place.fuzzy_score

        # Den längeren Text als Repräsentation behalten
        if len(place.text) > len(existing.text):
            existing.text = place.text

    return sorted(
        merged,
        key=lambda p: (p.start, p.end),
    )


def find_places_basic_with_gazetteer(
    text: str,
    source: str = "video_description",
) -> list[PlaceMention]:
    """Erkennung inklusive Gazetteer-Abgleich."""

    places = find_places_basic(text, source)
    return match_gazetteer(places)


def extract_places(
    text: str,
    source: str = "video_description",
) -> PlaceExtractionResult:
    """Extrahiert Ortsangaben und Kreuzungsbeziehungen."""

    if not text or not text.strip():
        return PlaceExtractionResult()

    places = find_places_basic_with_gazetteer(text, source)

    relations = find_regex_relations(text, places)

    return PlaceExtractionResult(
        places=places,
        relations=relations,
    )
