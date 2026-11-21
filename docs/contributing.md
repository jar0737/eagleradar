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

**Where tasks live:** every piece of work is a **GitHub Issue** (templates: *Feature*, *Bug*);
its number is the task's unique ID. **Trello** is the team board for everything around the
issues (who works on what, meetings, research, deadlines).

1. Pick or create an **issue** in GitHub.
2. Create a branch from `main`, named `<type>/<issue-nr>-<short-name>`:

   | Type | Use it for | Example |
   |---|---|---|
   | `feature/` | New functionality | `feature/12-gazetteer` |
   | `fix/` | Bug fixes | `fix/31-street-abbreviations` |
   | `docs/` | Documentation only | `docs/18-setup-guide` |
   | `test/` | Tests or the evaluation set | `test/25-labelled-posts` |
   | `refactor/` | Restructuring without new behaviour | `refactor/40-split-db-queries` |
   | `chore/` | Setup, dependencies, CI, config | `chore/7-ci-python-312` |

   Lowercase English, words joined with hyphens, no spaces or umlauts. One branch = one issue.
3. Commit small steps with clear messages ([Conventional Commits](https://www.conventionalcommits.org/)):
   `feat(geo): build gazetteer`, `fix(nlp): handle "Str." abbreviation`, `docs: explain gazetteer`
4. Push and open a **pull request** (the template has a checklist). Write `Closes #<issue-nr>`
   in the description, so the issue closes when the pull request is merged.
5. At least **one approving review** by another team member, then merge. CI must be green.

`main` is protected by the ruleset `protect-main`: changes only via pull request with 1 approval
and green `lint` and `test` checks; no direct pushes, force pushes or deletion.

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
