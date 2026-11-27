import re

from eagleradar.nlp.place_mention import (
    IntersectionRelation,
    PlaceMention,
)

STREET_SUFFIXES = [
    "straße",
    "strasse",
    "str.",
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

STREET_SUFFIX_PATTERN = (
    r"(?:" + "|".join(re.escape(s) for s in sorted(STREET_SUFFIXES, key=len, reverse=True)) + r")"
)

# Beispiele:
# Friedrichstraße
# Leipziger Straße
STREET_NAME_PATTERN = (
    r"(?:"
    r"[A-ZÄÖÜ][\wäöüß-]*" + STREET_SUFFIX_PATTERN + r"|"
    r"[A-ZÄÖÜ][\wäöüß-]*\s+" + STREET_SUFFIX_PATTERN + r")"
)

STREET_PATTERN = re.compile(
    r"(?<!\w)" + STREET_NAME_PATTERN + r"(?!\w)",
    re.IGNORECASE,
)


STATION_NAME_TOKEN = (
    r"(?!(?i:und|oder|am|an|in|bei|auf|mit|von|zu|der|die|das|"
    r"steht|stehen|geht|gehts|fährt|ist|sind|richtung)\b)"
    r"[A-ZÄÖÜ][\wÄÖÜäöüß-]*"
)

STATION_PREFIX_PATTERN = re.compile(
    r"(?i:\b(?:Bahnhof|Bhf\.?|Bf\.?))"
    r"\s+" + STATION_NAME_TOKEN + r"(?:\s+" + STATION_NAME_TOKEN + r"){0,2}"
    r"(?=$|[.,!?;:]|\s)"
)

PUBLIC_TRANSPORT_PATTERN = re.compile(
    r"(?i:\b(?:U-Bahn|S-Bahn|U-Bhf\.?|S-Bhf\.?))"
    r"\s+" + STATION_NAME_TOKEN + r"(?:\s+" + STATION_NAME_TOKEN + r"){0,2}"
    r"(?=$|[.,!?;:]|\s)"
)

CONNECTOR_PATTERN = re.compile(
    r"^\s*(?P<connector>und|/|&)\s*$",
    re.IGNORECASE,
)


def find_regex_places(
    text: str,
    source: str = "video_description",
) -> list[PlaceMention]:
    """Erkennt Straßen- und Haltestellennamen mit Regex."""

    if not text or not text.strip():
        return []

    places = []

    def add_place(start, end, place_type):
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

    for match in STREET_PATTERN.finditer(text):
        add_place(match.start(), match.end(), "street")

    for match in STATION_PREFIX_PATTERN.finditer(text):
        add_place(match.start(), match.end(), "station")

    for match in PUBLIC_TRANSPORT_PATTERN.finditer(text):
        add_place(match.start(), match.end(), "station")

    # Doppelte Treffer anhand ihrer Textposition entfernen.
    unique_places = {}

    for place in places:
        key = (place.start, place.end)

        if key not in unique_places:
            unique_places[key] = place

    return sorted(
        unique_places.values(),
        key=lambda place: (place.start, place.end),
    )


def find_regex_relations(
    text: str,
    places: list[PlaceMention],
) -> list[IntersectionRelation]:
    """Erkennt Beziehungen zwischen zwei Straßen an Kreuzungen."""

    if not text or not places:
        return []

    streets = sorted(
        [place for place in places if place.type == "street"],
        key=lambda place: (place.start, place.end),
    )

    relations = []

    for first, second in zip(streets, streets[1:], strict=False):
        if first.end > second.start:
            continue

        between = text[first.end : second.start]
        connector_match = CONNECTOR_PATTERN.fullmatch(between)

        if connector_match is None:
            continue

        context_before = text[max(0, first.start - 25) : first.start]

        has_intersection_context = re.search(
            r"\b(?:Ecke|Kreuzung|an\s+der)\s*$",
            context_before,
            re.IGNORECASE,
        )

        connector = connector_match.group("connector").casefold()

        # "und" allein ist kein ausreichender Hinweis auf eine Kreuzung.
        # "/" und "&" gelten als explizite Verknüpfung.
        if not has_intersection_context and connector == "und":
            continue

        relations.append(
            IntersectionRelation(
                street1=first.normalized_name,
                street2=second.normalized_name,
                street1_start=first.start,
                street1_end=first.end,
                street2_start=second.start,
                street2_end=second.end,
                connector=connector,
                start=first.start,
                end=second.end,
                detected_by=["regex"],
                confidence=(0.9 if has_intersection_context else 0.8),
            )
        )

    return relations
