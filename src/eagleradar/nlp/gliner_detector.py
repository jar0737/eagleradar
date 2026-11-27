from gliner import GLiNER

from eagleradar.nlp.place_mention import PlaceMention

MODEL_NAME = "VAGOsolutions/SauerkrautLM-GLiNER"

LABELS = [
    "street",
    "station",
    "district",
    "landmark",
    "geographical location",
]

LABEL_MAPPING = {
    "street": "street",
    "station": "station",
    "district": "district",
    "landmark": "landmark",
    "geographical location": "geographical_location",
}


_model = None


def load_model():
    global _model

    if _model is None:
        _model = GLiNER.from_pretrained(MODEL_NAME)

    return _model


def find_gliner_places(
    text: str,
    source: str = "video_description",
    threshold: float = 0.3,
) -> list[PlaceMention]:
    if not text or not text.strip():
        return []

    model = load_model()

    entities = model.predict_entities(
        text,
        LABELS,
        threshold=threshold,
    )

    places = []

    for entity in entities:
        label = entity["label"]

        # GLiNER-Label auf unseren PlaceMention-Typ abbilden
        place_type = LABEL_MAPPING.get(label)

        if place_type is None:
            continue

        start = entity["start"]
        end = entity["end"]

        places.append(
            PlaceMention(
                text=text[start:end],
                normalized_name=text[start:end],
                type=place_type,
                start=start,
                end=end,
                detected_by=["gliner"],
                confidence=float(entity["score"]),
                source=source,
            )
        )

    return places
