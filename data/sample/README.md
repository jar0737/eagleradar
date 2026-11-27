# Sample data

`gazetteer.csv` is the exception in this folder: **real** place data for Berlin (streets, stations,
landmarks, localities, districts), not synthetic. Streets, stations and landmarks: © OpenStreetMap contributors, ODbL 1.0.
Sources and how to rebuild it: `docs/data-and-privacy.md`, section "Geodata".

Put the small, **synthetic** demo dataset here (it is committed to Git).
Real social media data goes to `data/raw/`, which is git-ignored.

Suggested input format (agree on it as a team): one record per post with
`id`, `text`, `timestamp` (ISO 8601), `source`, and optionally `author` (pseudonymized),
`url`, `image_paths`.
