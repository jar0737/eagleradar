# Architecture

> Template – fill in as the design takes shape.

## Overview

<!-- Diagram of the pipeline: import → NLP / CV → geocoding → clustering → map -->

## Modules

| Module | Responsibility | Input | Output |
|---|---|---|---|
| `ingest/` | | | |
| `nlp/` | | | |
| `vision/` | | | |
| `geo/` | Turn place names into coordinates, offline (see below) | `place_mentions.mention_text` | `place_mentions.geom`, `geocode_status` |
| `clustering/` | | | |
| `app.py` | | | |

### `geo/`: geocoding

1. `scripts/build_gazetteer.py` builds `data/sample/gazetteer.csv` (about 15,000 places) from the
   downloads listed in [data-and-privacy.md](data-and-privacy.md#geodata). Needed only for updates.
2. `python -m eagleradar.geo.gazetteer` loads the list into the table `places`.
3. `python -m eagleradar.geo.geocoder` geocodes all mentions that have no coordinates yet.
   In code: `geocode_mentions(conn)`, or `Geocoder(places).geocode(name, hints)` for one name.

| Result (`geocode_status`) | Meaning | Coordinates |
|---|---|---|
| `found` | one place fits | yes, `geocoded_by = 'gazetteer'` |
| `ambiguous` | several places fit ("Hauptstraße"), `Result.candidates` lists them | no |
| `unknown` | not in the list | no |

- Names are compared with `normalize()` ("Tiergartenstr." = "Tiergartenstraße"). Inflected forms
  ("Argentinischen Allee") and house numbers are handled. **`nlp/` should use the same function.**
- A street that runs through several localities is one place (`places.part`);
  its coordinates are in the longest section.
- A locality or district mentioned in the same post decides between several places.
- The view `posts_without_place` lists all posts that cannot be shown on the map, with the reason.

## Data model

<!-- Which fields does a post have? What does a detected location look like? -->

## Design decisions

| Decision | Alternatives considered | Reason |
|---|---|---|
| Streamlit for the web app | Flask/FastAPI + React | |
| Local gazetteer for geocoding | Nominatim only | works offline (FA-06), no request limit |
| Ambiguous names get no coordinates | prefer Steglitz-Zehlendorf | a wrong marker could send help to the wrong place |
| | | |

## Known limitations
