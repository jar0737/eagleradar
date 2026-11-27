from eagleradar.nlp.text_normalizer import normalize_text


def test_normalize_whitespace():
    text = "Bhf    Südkreuz"

    result = normalize_text(text)

    assert result == "Bhf    Südkreuz"
    assert len(result) == len(text)


def test_normalize_leading_and_trailing_whitespace():
    text = "  Kotti  "

    result = normalize_text(text)

    assert result == "  Kotti  "
    assert len(result) == len(text)


def test_normalize_empty_text():
    assert normalize_text("") == ""


def test_normalize_none_like_empty_input():
    assert normalize_text(None) == ""


def test_normalize_preserves_capitalization():
    text = "Bhf Südkreuz"

    result = normalize_text(text)

    assert result == "Bhf Südkreuz"


def test_normalize_preserves_umlauts():
    text = "Görlitzer Bahnhof"

    result = normalize_text(text)

    assert result == "Görlitzer Bahnhof"
