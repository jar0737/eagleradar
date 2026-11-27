from dataclasses import dataclass

from rapidfuzz import fuzz, process


@dataclass
class GazetteerEntry:
    official_name: str
    aliases: list[str]
    type: str


GAZETTEER = [
    GazetteerEntry(official_name="Kottbusser Tor", aliases=["kotti"], type="station"),
    GazetteerEntry(
        official_name="Kottbusser Tor",
        aliases=["kotti"],
        type="intersection",
    ),
    GazetteerEntry(official_name="Görlitzer Bahnhof", aliases=["görli"], type="station"),
    GazetteerEntry(
        official_name="Zoologischer Garten", aliases=["zoo", "zoologischer garten"], type="station"
    ),
    GazetteerEntry(official_name="Alexanderplatz", aliases=["alex"], type="station"),
    GazetteerEntry(
        official_name="Nollendorfplatz", aliases=["Nolle", "Noll", "Nolli"], type="station"
    ),
    GazetteerEntry(official_name="Schlesisches Tor", aliases=["schlesi"], type="station"),
]


def find_gazetteer_match(name: str) -> GazetteerEntry | None:
    search_name = normalize(name)

    for entry in GAZETTEER:
        if normalize(entry.official_name) == search_name:
            return entry

        for alias in entry.aliases:
            if normalize(alias) == search_name:
                return entry

    return None


def normalize(name: str) -> str:
    return name.strip().casefold()


def find_fuzzy_match(name: str, threshold: float = 85) -> tuple[GazetteerEntry, float] | None:
    search_name = normalize(name)

    if not search_name:
        return None

    # Offizielle Namen und Aliases als Suchmöglichkeiten sammeln
    choices = {}

    for entry in GAZETTEER:
        choices[entry.official_name] = entry

        for alias in entry.aliases:
            choices[alias] = entry

    # Ähnlichsten Namen suchen
    match = process.extractOne(
        search_name,
        list(choices.keys()),
        scorer=fuzz.ratio,
        score_cutoff=threshold,
    )

    if match is None:
        return None

    matched_name, score, _ = match

    return choices[matched_name], score
