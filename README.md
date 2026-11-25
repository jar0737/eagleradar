# 🦅 EagleRadar

**Detecting and mapping location hints in social media posts.**
Use case: the power outage in south-west Berlin (Steglitz-Zehlendorf) in January 2026.

EagleRadar will import public social media posts, recognise **event types** and **place
mentions** in text (NLP) and images (computer vision), geocode them, group similar
posts, detect duplicates and show them as markers on an interactive map with
**time, source and type**.

> Student project (Wirtschaftsinformatik-Projekt).

## Requirements

| Requirement | Module | Status |
|---|---|---|
| Import posts (dataset; optionally an allowed live API) | `ingest/` | ⬜ open |
| Detect place mentions in text (NLP) | `nlp/` | ⬜ open |
| Detect event types | `nlp/` | ⬜ open |
| Detect place names in images / video (CV) | `vision/` | ⬜ open |
| Geocode place names (e.g. "Tiergartenstr.") | `geo/` | ✅ done |
| Group similar posts, detect duplicates | `clustering/` | ⬜ open |
| Map markers with source, time and type | `app.py` | ⬜ open |

## Quick start

Requirements: [Git](https://git-scm.com/) and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/<user>/eagleradar.git
cd eagleradar
uv sync                                          # installs Python + dependencies
uv run pytest                                    # run the tests
uv run streamlit run src/eagleradar/app.py       # opens http://localhost:8501
```

### Optional extras (heavy ML libraries)

```bash
uv sync --extra vision       # OCR (EasyOCR, OpenCV)
uv sync --extra nlp          # spaCy, then: uv run python -m spacy download de_core_news_lg
uv sync --extra embeddings   # sentence-transformers
uv sync --extra osm          # OpenStreetMap data (osmnx, geopandas)
```

On Linux without an NVIDIA GPU, the `vision` extra downloads a large CUDA build of
PyTorch. See the uv guide "Using uv with PyTorch" for the CPU-only setup.

## Project structure

```
src/eagleradar/
  app.py          Streamlit web app
  ingest/         import posts
  nlp/            event types, place mentions in text
  vision/         place names in images / video
  geo/            geocoding
  clustering/     duplicates, groups
scripts/          helper scripts (data preparation, evaluation)
tests/            pytest
data/sample/      small committed demo data (everything else in data/ is git-ignored)
docs/             detailed documentation
```

## Development

```bash
uv run pytest                 # tests
uv run ruff check . --fix     # lint
uv run ruff format .          # format
uv run pre-commit install     # run checks automatically before each commit
uv add <package>              # add a dependency (commit pyproject.toml + uv.lock)
```

GitHub Actions runs lint and tests on every push and pull request. Workflow: [docs/contributing.md](docs/contributing.md)

## Documentation

- [Architecture](docs/architecture.md)
- [Data and privacy](docs/data-and-privacy.md)
- [Evaluation](docs/evaluation.md)
- [Contributing](docs/contributing.md)

## Team

| Name | Module / role |
|---|---|
| … | … |

## License

To be decided by the team.
