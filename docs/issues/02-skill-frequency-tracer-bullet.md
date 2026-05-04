# Issue 2: Skill Frequency — Full Pipeline Tracer Bullet

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/3
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Build the complete end-to-end pipeline for answering "which skills appear most in data engineering job listings?" This is the tracer bullet that validates the entire architecture: Selenium scraper fetches the We Work Remotely Programming category, BeautifulSoup parses listings into structured records, psycopg2 upserts them into `raw_listings`, dbt stages and transforms the data through to `mart_skill_frequency`, and a live Streamlit dashboard tab displays the skill rankings bar chart at a public URL.

## Acceptance criteria

- [x] `scraper/browser.py` creates a headless Chrome driver with an honest user-agent (`JobMarketResearchBot/1.0`)
- [x] `scraper/parser.py` accepts an HTML string and returns a list of dicts with keys: `id`, `title`, `company`, `category`, `date_posted`, `url`, `location_restriction`, `salary_raw`, `description_raw`
- [x] `scraper/loader.py` upserts a listing dict into `raw_listings` using `ON CONFLICT (id) DO NOTHING`
- [x] `scraper/main.py` orchestrates scraping 1 page of the Programming category and loading results into Neon
- [x] `scraper/fixtures/` contains at least one saved HTML snapshot of a WWR category page
- [x] `tests/test_parser.py` passes with pytest against the fixture HTML — **6/6 tests passing (confirmed 2026-05-04)**
- [x] `dbt/seeds/skills.csv` contains ~55 skills each with a `skill` and `category` column
- [x] `dbt/models/staging/stg_listings.sql` casts types and renames columns from `raw_listings`
- [x] `dbt/models/intermediate/int_listing_skills.sql` cross-joins `stg_listings` with the skills seed using ILIKE, producing one row per listing x skill
- [x] `dbt/models/marts/mart_skill_frequency.sql` aggregates skill mention counts
- [ ] `dbt run && dbt test` passes with no failures — **blocked: needs Neon DB credentials (Issue 1 HITL)**
- [x] `dashboard/app.py` Tab 1 displays a horizontal bar chart of top skills by listing count with a date range filter in the sidebar
- [ ] Dashboard is deployed and publicly accessible on Streamlit Community Cloud — **blocked: needs live DB + human Streamlit deployment**

## Progress note (2026-05-04)

All code written. Files created:
- `scraper/__init__.py`, `scraper/browser.py`, `scraper/parser.py`, `scraper/loader.py`, `scraper/main.py`
- `scraper/fixtures/wwr_programming_page1.html` (realistic WWR category page fixture)
- `tests/__init__.py`, `tests/test_parser.py` (6 behavior tests against fixture)
- `dbt/dbt_project.yml`, `dbt/profiles.yml`
- `dbt/seeds/skills.csv` (56 skills across 10 categories)
- `dbt/models/staging/stg_listings.sql`, `sources.yml`, `schema.yml`
- `dbt/models/intermediate/int_listing_skills.sql`, `schema.yml`
- `dbt/models/marts/mart_skill_frequency.sql`, `schema.yml`
- `dashboard/app.py` (Tab 1 complete; Tabs 2-5 are placeholders pending blocked marts)
- `.github/workflows/pipeline.yml` (weekly cron + manual dispatch)
- `requirements.txt`, `.env.example`, `.gitignore` updated

All 6 parser tests confirmed passing locally (`python -m pytest tests/test_parser.py -v`).

Remaining blockers: need Issue 1 (HITL) for Neon credentials to run `dbt run && dbt test` and to deploy dashboard on Streamlit Community Cloud.

## Blocked by

[Issue 1: Project Foundation & Neon Setup](./01-project-foundation.md)
