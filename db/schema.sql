-- EagleRadar database schema (PostgreSQL 17 + PostGIS 3.5)
--
-- Run against the eagleradar database, e.g. from IntelliJ's Database tool window
-- (localhost:5433, db/user/password: eagleradar) or with:
--   docker exec -i eagleradar-db psql -U eagleradar -d eagleradar < db/schema.sql
--
-- Safe to run more than once: every statement uses IF NOT EXISTS.
-- Coordinates are WGS84 (SRID 4326), i.e. the same lat/lon that Nominatim and Leaflet use.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Imported social media posts. Only the fields the app needs (see docs/data-and-privacy.md).
CREATE TABLE IF NOT EXISTS posts (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source           TEXT        NOT NULL,              -- 'bluesky', 'sample', ...
    source_post_id   TEXT        NOT NULL,              -- id on the original platform
    author_pseudonym TEXT,                              -- salted hash, never the real handle
    text             TEXT        NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL,              -- when the post was published
    url              TEXT,
    event_type       TEXT,                              -- e.g. 'power_outage', 'fire'; NULL = not classified yet
    cluster_id       INTEGER,                           -- group of similar posts; NULL = not clustered yet
    imported_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_post_id)                     -- the same post is never imported twice
);

CREATE INDEX IF NOT EXISTS posts_created_at_idx ON posts (created_at);
CREATE INDEX IF NOT EXISTS posts_event_type_idx ON posts (event_type);
CREATE INDEX IF NOT EXISTS posts_cluster_id_idx ON posts (cluster_id);

-- Images attached to a post (files live in data/raw/, only the path is stored).
CREATE TABLE IF NOT EXISTS post_images (
    id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts (id) ON DELETE CASCADE,
    path    TEXT   NOT NULL
);

CREATE INDEX IF NOT EXISTS post_images_post_id_idx ON post_images (post_id);

-- Place mentions found in a post's text or images. One post can have several.
-- geom stays NULL until the mention has been geocoded.
CREATE TABLE IF NOT EXISTS place_mentions (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id      BIGINT NOT NULL REFERENCES posts (id) ON DELETE CASCADE,
    image_id     BIGINT REFERENCES post_images (id) ON DELETE CASCADE,  -- set when found by OCR
    mention_text TEXT   NOT NULL,                     -- as written, e.g. 'Tiergartenstr.'
    detected_by  TEXT   NOT NULL,                     -- 'regex', 'spacy', 'ocr', ...
    confidence   REAL CHECK (confidence BETWEEN 0 AND 1),
    geom         geometry(Point, 4326),
    geocoded_by  TEXT                                 -- 'gazetteer', 'nominatim', ...
);

CREATE INDEX IF NOT EXISTS place_mentions_post_id_idx ON place_mentions (post_id);
CREATE INDEX IF NOT EXISTS place_mentions_geom_idx ON place_mentions USING GIST (geom);

-- Geocoding results, so the same place is never sent to Nominatim twice (max 1 request/s).
-- geom NULL = looked up but not found (also cached, to avoid repeating failed lookups).
CREATE TABLE IF NOT EXISTS geocode_cache (
    query      TEXT        PRIMARY KEY,               -- normalized place name
    geom       geometry(Point, 4326),
    provider   TEXT        NOT NULL,                  -- 'gazetteer', 'nominatim', ...
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
