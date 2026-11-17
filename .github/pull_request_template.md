<!--
PR title: <type>(<module>): short description (#issue)
e.g. feat(geo): gazetteer from Berlin open data (#12)
Replace every comment below; delete sections that don't apply.
-->

## What does this change?

<!-- 1–3 sentences: what changed and why. Link the task: Closes #12, or the Trello card link. -->

**Part / module:** <!-- e.g. Part 2 – Database (db/) -->

## How to test it

<!--
Exact steps the reviewer runs on their own machine, and what they should see. Example:
1. git switch feature/12-geo-gazetteer && uv sync
2. docker compose up -d
3. uv run pytest
Expected: all tests pass; the map shows the new markers.
-->

## Checklist

- [ ] Branch name follows `<type>/<issue-nr>-<module>-<short-description>`
- [ ] `uv run pytest` passes locally
- [ ] New behaviour has a test in `tests/`
- [ ] Documentation updated (README or `docs/`) in this PR
- [ ] New dependencies added with `uv add` (`pyproject.toml` and `uv.lock` committed)

### Database (only if this PR touches the database)

- [ ] Schema changes are in `db/schema.sql` and safe to run twice (`IF NOT EXISTS`)
- [ ] `tests/test_db.py` covers the change
- [ ] Team setup guide updated if teammates must do something (e.g. re-run the schema)

### Data and privacy (rules: `docs/data-and-privacy.md`)

- [ ] No `.env`, passwords, API keys or salts committed
- [ ] No real social media data or author handles (only synthetic data in `data/sample/`)
- [ ] Screenshots use synthetic data only

## Notes for the reviewer

<!-- What to look at closely, open questions, screenshots for UI changes. -->
