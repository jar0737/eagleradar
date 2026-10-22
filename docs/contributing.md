# Contributing

## First-time setup

```bash
git clone https://github.com/<user>/eagleradar.git && cd eagleradar
uv sync                         # core + dev tools
uv run pre-commit install       # lint/format automatically before every commit
cp .env.example .env            # only needed for Bluesky / online geocoding
uv run pytest                   # everything green? You're ready.
```

## Workflow

1. Pick or create an **issue** in GitHub (templates: *Feature*, *Bug*).
2. Create a branch from `main`:
   `feature/<issue-nr>-short-name`, `fix/<issue-nr>-short-name`, `docs/...`
3. Commit small steps with clear messages:
   `feat: add OCR for video frames`, `fix: handle empty upload`, `docs: explain gazetteer`
4. Push and open a **pull request** (the template has a checklist).
5. At least **one review** by another team member, then merge. CI must be green.
6. `main` is protected: no direct pushes.

GitHub settings to enable once (admin): *Settings → Branches → Add branch ruleset* for `main`:
require a pull request before merging (1 approval) and require status checks to pass (`lint`, `test`).

## Module ownership

One owner per module keeps merge conflicts rare. The owner reviews changes to
their module and keeps its section in `docs/` up to date.

| Module | Owner |
|---|---|
| `ingest/` | … |
| `nlp/` | … |
| `vision/` | … |
| `geo/` | … |
| `clustering/` | … |
| `app.py` | … |
| docs / evaluation | … |

## Rules of thumb

- New dependency → `uv add <pkg>` (or `uv add --optional <extra> <pkg>` for heavy ML libraries);
  commit `pyproject.toml` **and** `uv.lock`.
- New behaviour → a test in `tests/`. Tests must run offline and without the extras.
- Documentation changes go in the **same pull request** as the code.
- Keep the README short; details belong in `docs/`.
- Never commit `.env`, real social media data or large files (> 2 MB, checked by pre-commit).
