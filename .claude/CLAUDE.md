# CLAUDE.md

## Project overview

Weekly ETL pipeline: scrapes data engineering job listings from We Work Remotely → loads raw data into PostgreSQL on Neon → transforms with dbt → visualizes in a public Streamlit dashboard.

**Modules:**
- `scraper/` — Playwright browser context, BeautifulSoup parser, Postgres loader, orchestration entry point
- `dbt/` — staging / intermediate / mart models, skills seed
- `dashboard/` — Streamlit single-page app with 5 tabs
- `tests/` — pytest unit tests (no network, no DB)
- `Dockerfile` — scraper + dashboard container (Python 3.12, xvfb for headed Chromium)

## Architecture decisions

- **ELT, not ETL** — raw data lands as-is (`salary_raw`, `description_raw` are plain text). All parsing and transformation is owned by dbt.
- **Skills via seed cross-join** — `dbt/seeds/skills.csv` cross-joined with listings using PostgreSQL word-boundary regex (`~*`). No NLP. To add a skill, add a row to the CSV and run `dbt seed`.
- **Idempotent upsert** — `ON CONFLICT (id) DO UPDATE SET ... COALESCE(EXCLUDED.x, raw_listings.x)` enriches existing rows with detail-page data without overwriting good data with nulls.
- **Two-pass scraping** — index page gives listing metadata; detail page gives `description_raw` and fallback salary. Fields from the index page take precedence over detail page fields.
- **Bot detection bypass** — browser runs headed (not headless) with `playwright-stealth` fingerprint suppression. In CI and Docker, `xvfb` provides a virtual display. Do not switch to headless mode — Cloudflare will block it.
- **Neon connection keep-alive** — `SELECT 1` ping every 5 listings in `scraper/main.py` because Neon drops idle connections after ~5 minutes.

## Environment

- **Python**: 3.12 (requirements.txt frozen against this version — do not use 3.10/3.11 base images)
- **Virtual environment**: `.venv-dbt`
- **Secrets**: all via environment variables; never committed. Local dev uses `.env` (see `.env.example`).

## Running things locally

```bash
# Tests (fast, no network)
pytest tests/ -v

# Scraper
python -m scraper.main

# dbt (from dbt/ directory)
dbt seed && dbt run && dbt test

# Dashboard
streamlit run dashboard/app.py
```

See `docs/commands.md` for the full command reference including Docker commands.

## Docker

The container uses `python:3.12-slim-bookworm` with Playwright Chromium + xvfb + xauth installed. The scraper runs headed inside xvfb (`SCRAPER_HEADLESS=false`, `DISPLAY=:99`).

```bash
docker build -t job-market-scraper .
docker run --env-file .env job-market-scraper                          # scraper
docker run --env-file .env -p 8501:8501 job-market-scraper \
  streamlit run dashboard/app.py --server.address=0.0.0.0             # dashboard
```

## Testing conventions

- Tests live in `tests/`, use pytest, and must not require network or DB access.
- Parser tests use saved HTML fixtures in `scraper/fixtures/`.
- Loader tests mock the DB connection with `unittest.mock.MagicMock`.
- Config tests use `ast.parse` to assert constants in source files without importing them.
- `loader._batch` is module-level state — tests must call `loader_module._batch.clear()` in `setup_function()`.

## dbt conventions

- Staging models: views, light cleaning only
- Intermediate models: views, cross-joins and joins
- Mart models: tables, final analytical grain
- Schema tests on `stg_listings.id` (`not_null`, `unique`) and `int_listing_skills.skill` (`not_null`)

## What not to do

- Do not switch Playwright to headless mode — bot detection will block it.
- Do not add a `Data Science` key to `CATEGORY_SOURCES` in `scraper/main.py` without updating `test_scraper_config.py` — the test asserts exactly `["programming"]`.
- Do not use Python < 3.12 in Docker or CI — `networkx==3.6.1` and `dbt-core==1.11.8` require `>=3.11`, and requirements were frozen on 3.12.
- Do not remove `ttl=300` from `@st.cache_resource` in `dashboard/app.py` — Neon drops idle connections and the dashboard will silently break without it.
