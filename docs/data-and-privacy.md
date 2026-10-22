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

## External services

| Service | Used for | Policy notes |
|---|---|---|
| Nominatim (OpenStreetMap) | geocoding | max 1 request/s, meaningful user agent, cache results |
| Map tiles (OSM / CARTO) | map background | show attribution in the app |
| Streamlit | web framework | usage statistics disabled in `.streamlit/config.toml` |
