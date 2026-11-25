import re
from typing import Literal

from eagleradar.nlp.place_mention import PlaceMention

STREET_SUFFIXES = [
    "straße",
    "str.",
    "strasse",
    "str",
    "chaussee",
    "weg",
    "platz",
    "ufer",
    "ring",
    "gasse",
    "damm",
    "allee",
    "pfad",
    "steig",
    "promenade",
    "bogen",
    "zeile",
    "korso",
]


STREET_PATTERN = re.compile(
    r"\b"
    r"(?!(?:auf|an|in|der|die|das|dem|den|am|zum|zur)\b)"
    r"[A-ZÄÖÜ][\wÄÖÜäöüß-]*"
    r"(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß-]*){0,2}"
    r"\s+(?:" + "|".join(re.escape(suffix) for suffix in STREET_SUFFIXES) + r")" + r"(?!\w)",
    re.IGNORECASE,
)

STATION_NAME_TOKEN = (
    r"(?!(?:und|oder|am|an|in|bei|auf|mit|von|zu|der|die|das)\b)" r"[A-ZÄÖÜ][\wÄÖÜäöüß-]*"
)

# Bahnhof-Bezeichnungen
STATION_PREFIX_PATTERN = re.compile(
    r"\b(?:Bahnhof|Bhf\.?|Bf\.?)"
    r"\s+" + STATION_NAME_TOKEN + r"(?:\s+" + STATION_NAME_TOKEN + r"){0,2}"
    r"(?=$|[.,!?;:]|\s)",
    re.IGNORECASE,
)

# U-Bahn- und S-Bahn-Bezeichnungen
PUBLIC_TRANSPORT_PATTERN = re.compile(
    r"\b(?:U-Bahn|S-Bahn|U-Bhf\.?|S-Bhf\.?|U|S)"
    r"\s+" + STATION_NAME_TOKEN + r"(?:\s+" + STATION_NAME_TOKEN + r"){0,2}"
    r"(?=$|[.,!?;:]|\s)",
    re.IGNORECASE,
)

INTERSECTION_PATTERN = re.compile(
    r"\b(?:Ecke|Kreuzung)\s+"
    r"(?P<street1>.+?)"
    r"\s*(?:/|&|\bund\b)\s*"
    r"(?P<street2>.+?)"
    r"(?=$|[!?;])",
    re.IGNORECASE,
)

PlaceSource = Literal[
    "video_description",
    "voice_to_text",
    "hashtag_names",
    "ocr",
]


def find_regex_places(text: str, source: PlaceSource = "video_description") -> list[PlaceMention]:
    if not text or not text.strip():
        return []

    places = []

    def add_place(start: int, end: int, place_type: str) -> None:
        mention_text = text[start:end]

        places.append(
            PlaceMention(
                text=mention_text,
                normalized_name=mention_text,
                type=place_type,
                start=start,
                end=end,
                detected_by=["regex"],
                confidence=0.9,
                source=source,
            )
        )

    # Intersections: extract both streets separately
    for match in INTERSECTION_PATTERN.finditer(text):
        start = match.start()
        end = match.end()

        # Extract the complete intersection expression
        intersection_text = text[start:end]

        # Remove the introductory word "Ecke" or "Kreuzung"
        prefix_match = re.match(
            r"(?:Ecke|Kreuzung)\s+",
            intersection_text,
            re.IGNORECASE,
        )

        if prefix_match:
            start += prefix_match.end()

        add_place(start, end, "intersection")

    # Station prefixes
    for match in STATION_PREFIX_PATTERN.finditer(text):
        add_place(match.start(), match.end(), "station")

    # Public transport stations
    for match in PUBLIC_TRANSPORT_PATTERN.finditer(text):
        add_place(match.start(), match.end(), "station")

    # Street names
    for match in STREET_PATTERN.finditer(text):
        add_place(match.start(), match.end(), "street")

    # Remove duplicate matches while preserving detection order
    unique_places = {}

    for place in places:
        key = (place.start, place.end)
        unique_places[key] = place

    return list(unique_places.values())
