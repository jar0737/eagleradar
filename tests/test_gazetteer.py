from eagleradar.nlp.gazetteer import find_fuzzy_match, find_gazetteer_match


def test_find_alias_kotti():
    result = find_gazetteer_match("Kotti")

    assert result is not None
    assert result.official_name == "Kottbusser Tor"
    assert result.type == "station"


def test_find_alias_case_insensitive():
    result = find_gazetteer_match("KOTTI")

    assert result is not None
    assert result.official_name == "Kottbusser Tor"


def test_find_official_name():
    result = find_gazetteer_match("Alexanderplatz")

    assert result is not None
    assert result.official_name == "Alexanderplatz"
    assert result.type == "station"


def test_find_alias_with_different_case():
    result = find_gazetteer_match("nOlLe")

    assert result is not None
    assert result.official_name == "Nollendorfplatz"


def test_unknown_place_returns_none():
    result = find_gazetteer_match("Unbekannter Ort")

    assert result is None


def test_find_alias_schlesi():
    result = find_gazetteer_match("schlesi")

    assert result is not None
    assert result.official_name == "Schlesisches Tor"


def test_find_official_name_with_whitespace():
    result = find_gazetteer_match("  Görlitzer Bahnhof  ")

    assert result is not None
    assert result.official_name == "Görlitzer Bahnhof"


def test_fuzzy_match_finds_typo():
    result = find_fuzzy_match("Alexanderplaz")

    assert result is not None
    entry, score = result

    assert entry.official_name == "Alexanderplatz"
    assert score >= 85


def test_fuzzy_match_finds_station_typo():
    result = find_fuzzy_match("Görlitzer Bahnhoff")

    assert result is not None
    entry, score = result

    assert entry.official_name == "Görlitzer Bahnhof"
    assert score >= 85


def test_fuzzy_match_returns_none_for_unknown_name():
    result = find_fuzzy_match("xyzabc123")

    assert result is None


def test_fuzzy_match_returns_none_for_empty_name():
    assert find_fuzzy_match("") is None
