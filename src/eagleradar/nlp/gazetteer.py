from dataclasses import dataclass


@dataclass
class GazetteerEntry:
    official_name: str
    aliases: list[str]
    type: str


GAZETTEER = [
    GazetteerEntry(official_name="Kottbusser Tor", aliases=["kotti"], type="Intersection"),
    GazetteerEntry(official_name="Rosenthaler Platz", aliases=["rosi"], type="intersection"),
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
