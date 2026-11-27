# Data and privacy

Team rules for handling social media data. Check them with your supervisor and adjust.

## Principles (GDPR / DSGVO)

1. **Only public posts** from platforms whose terms allow API access for this purpose.
2. **Data minimization:** store only what the app needs (id, text, time, platform, link,
   images) – no follower counts, profiles or contact data.
3. **Pseudonymization on import:** replace author handles with a non-reversible pseudonym.
   Any secret (e.g. a salt) lives in `.env` and is never committed.
4. **No real data in Git:** only `data/sample/` (synthetic) is versioned; `data/raw/`
   and `data/processed/` are git-ignored.
5. **Purpose limitation:** data is used only for this project and deleted at the end.
6. Screenshots for slides and the report use **synthetic** data only.

## Live data (e.g. Bluesky)

- Use an **app password**, never your main password. Credentials go in `.env`.
- Fetch only the time window and keywords you need.
- Downloaded files go to `data/raw/` (git-ignored).

## Geodata

The gazetteer `data/sample/gazetteer.csv` is built from these downloads with
`scripts/build_gazetteer.py`. Put them in `data/raw/geo/` (git-ignored).

| Download | Content | Source | Licence |
|---|---|---|---|
| [`berlin-*-free.shp.zip`](https://download.geofabrik.de/europe/germany/berlin.html) (keep it zipped) | Streets, stations, landmarks | OpenStreetMap, extract by Geofabrik | [ODbL 1.0](https://www.openstreetmap.org/copyright) |
| [`bezirke.json`](https://gdi.berlin.de/geonetwork/srv/api/records/ced31d7d-353d-373a-b9a9-2251b9498bc0) | 12 districts | ALKIS Berlin Bezirke, Geoportal Berlin | [dl-de/zero-2-0](https://www.govdata.de/dl-de/zero-2-0) |
| [`ortsteile.json`](https://gdi.berlin.de/geonetwork/srv/api/records/61bd3084-c4b0-34e4-9a00-01daabb315f5) | 97 localities | ALKIS Berlin Ortsteile, Geoportal Berlin | [dl-de/zero-2-0](https://www.govdata.de/dl-de/zero-2-0) |

The two GeoJSON files come from the WFS services `alkis_bezirke` and `alkis_ortsteile` on
`gdi.berlin.de` (`OUTPUTFORMAT=application/json`, `SRSNAME=EPSG:4326`).

Streets, stations and landmarks are derived from OpenStreetMap: the file stays under the
ODbL, whatever licence the project gets, and the app must show
"© OpenStreetMap contributors" with a link to the copyright page.

The gazetteer contains no personal data.

## External services

| Service | Used for | Policy notes |
|---|---|---|
| Nominatim (OpenStreetMap) | geocoding | max 1 request/s, meaningful user agent, cache results |
| Map tiles (OSM / CARTO) | map background | show attribution in the app |
| Streamlit | web framework | usage statistics disabled in `.streamlit/config.toml` |
