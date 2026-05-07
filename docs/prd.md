# PRD: Job Market Analysis Tool

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/1

## Problem Statement

As a data engineering job seeker or hiring manager, there is no easy way to see which tools, skills, and technologies are actually being demanded by employers right now. Job boards surface individual listings, but offer no aggregated view of market trends — which skills are rising, which are declining, how salary correlates with skill set, and which industries are hiring most actively. A candidate preparing for interviews or deciding what to learn next has no data-driven way to answer these questions.

## Solution

A scheduled ETL pipeline that scrapes data engineering job listings from We Work Remotely, normalizes and loads them into a PostgreSQL database on Neon, and transforms them with dbt into analytical views. A Streamlit dashboard deployed on Streamlit Community Cloud surfaces the findings publicly, enabling anyone to explore real-time job market intelligence: which tools employers actually want, salary ranges by skill, hiring volume by category, week-over-week demand shifts, and which skills cluster together in job descriptions.

## User Stories

1. As a data engineering job seeker, I want to see which tools appear most frequently in job descriptions, so that I can prioritize what to learn.
2. As a data engineering job seeker, I want to filter skill frequency by date range, so that I can see recent demand rather than historical noise.
3. As a data engineering job seeker, I want to see how salary ranges vary by required skill set, so that I can understand which skills command higher pay.
4. As a data engineering job seeker, I want to see a data coverage indicator on the salary chart, so that I know how representative the salary data is.
5. As a data engineering job seeker, I want to see which industries and categories are hiring most actively, so that I can target my applications.
6. As a data engineering job seeker, I want to see how demand for specific skills has shifted week over week, so that I can spot emerging trends.
7. As a data engineering job seeker, I want to compare multiple skills on a single trend chart, so that I can see relative growth or decline side by side.
8. As a data engineering job seeker, I want to see which skills co-occur most often in the same job listing, so that I can understand which tool combinations employers expect.
9. As a hiring manager, I want to see which skills are being required most broadly across data engineering roles, so that I can benchmark our job descriptions.
10. As a portfolio reviewer, I want to view a live public dashboard, so that I can see the tool working without setting up any infrastructure.
11. As a pipeline operator, I want the scraper to run automatically every week, so that the data stays current without manual intervention.
12. As a pipeline operator, I want only new listings to be scraped each run, so that the pipeline is efficient and avoids duplicate data.
13. As a pipeline operator, I want dbt tests to run after every pipeline execution, so that data quality issues are caught automatically.
14. As a pipeline operator, I want the pipeline to respect We Work Remotely's robots.txt and rate limits, so that scraping remains ethical and the IP is not blocked.
15. As a developer, I want to run the scraper locally against saved HTML fixtures, so that I can develop the parser without firing up a browser repeatedly.
16. As a developer, I want a Neon dev branch separate from production, so that I can develop dbt models without risking prod data.
17. As a developer, I want all secrets managed via environment variables and GitHub Secrets, so that no credentials are committed to the repository.
18. As a developer, I want the skills dictionary to be a dbt seed file, so that I can extend the skills list without changing any code.
19. As a developer, I want skills grouped by category (language, orchestration, warehouse, etc.), so that the dashboard can display grouped skill frequency charts.
20. As a developer, I want the raw listings stored as-is with salary and description as plain text, so that the dbt transformation layer owns all parsing logic.

## Implementation Decisions

### Modules

**Scraper (Python)**
- `scraper/browser.py` — Playwright persistent context lifecycle: creates a Chromium context backed by a persistent `browser_profile/` directory (stores Cloudflare `cf_clearance` cookie between runs), applies `playwright-stealth` fingerprint suppression, fetches page HTML with human scroll simulation, enforces 1.5-3 second random delays, and retries up to 3 times on bot challenge pages with 6-12 second exponential backoff
- `scraper/parser.py` — BeautifulSoup parsing: takes raw HTML string, returns a list of listing dicts with fields: id, title, company, category, date_posted, url, location_restriction, salary_raw, description_raw; handles both legacy `article.job` and new `li.new-listing-container` WWR markup; filters listings older than 7 days
- `scraper/loader.py` — Postgres upsert: takes a listing dict and a connection, inserts with `ON CONFLICT (id) DO NOTHING`; also owns table creation
- `scraper/main.py` — Orchestration entry point: initializes Playwright context, iterates over Programming and Data Science category pages (max 1 page each — WWR uses a single-page listing format), parses, deduplicates via DB lookup, loads new listings

**dbt Project**
- Staging layer: `stg_listings` — casts types, renames columns, light cleaning of `raw_listings`
- Intermediate layer: `int_listing_skills` — cross-joins `stg_listings` with the `skills` seed using PostgreSQL word-boundary regex matching (`~* ('\m' || skill || '\m')`), producing one row per listing x skill; regex prevents partial-word false positives (e.g. "Python" matching "Jython")
- Mart layer (5 models):
  - `mart_skill_frequency` — skill -> count of listings mentioning it, filterable by date
  - `mart_skill_salary` — skill -> min/avg/max salary extracted from salary_raw (sparse, includes coverage %)
  - `mart_industry_hiring` — category -> listing count by week
  - `mart_weekly_trends` — week x skill -> listing count (enables WoW delta calculation)
  - `mart_skill_cooccurrence` — skill_a x skill_b -> count of listings where both appear

**Seeds**
- `seeds/skills.csv` — ~85 skills with a `skill` column and a `category` column (language, processing, orchestration, warehouse, cloud, infrastructure, transformation, storage, visualization, library); expanded from the initial ~55 to include web, backend, ML/AI, and DevOps skills

**Dashboard (Streamlit)**
- `dashboard/app.py` — Single-file Streamlit app with 5 tabs: Skill Rankings (bar chart), Salary by Skill (bar chart with coverage caveat), Hiring by Category (bar chart), Week-over-Week Trends (line chart with multi-skill selector), Skill Co-occurrence (heatmap). Sidebar with global date range filter. Reads directly from Neon mart tables via psycopg2.

**CI/CD**
- `.github/workflows/pipeline.yml` — Weekly cron schedule (Monday 6am UTC), manual dispatch trigger, ubuntu-latest runner, Playwright Chromium browser setup, runs scraper then dbt (seed -> run -> test)

### Architectural Decisions

- **ELT pattern**: Raw data loaded as-is; all parsing and transformation owned by dbt. salary_raw and description_raw are plain text in the raw layer.
- **Listing ID deduplication**: Extracted from the We Work Remotely URL slug. Used as primary key with `ON CONFLICT DO NOTHING` for idempotent loads.
- **Rate limiting**: 1.5-3 second random sleep between page requests, max 1 page per category per run (WWR uses a single-page listing format with all current listings on one page).
- **Skill extraction via seed cross-join**: Skills matched using PostgreSQL word-boundary regex (`~*`) against description_raw. No NLP — deterministic, version-controlled, easy to extend.
- **Neon dev/prod branches**: Dev branch for local development and dbt experimentation; prod branch for GitHub Actions pipeline output.
- **Dashboard deployment**: Streamlit Community Cloud — free, public URL, auto-deploys from GitHub, secrets managed in their dashboard UI.

### Schema

```
raw_listings:
  id                   VARCHAR PRIMARY KEY
  title                VARCHAR NOT NULL
  company              VARCHAR
  category             VARCHAR
  date_posted          DATE
  url                  VARCHAR
  location_restriction VARCHAR
  salary_raw           VARCHAR
  description_raw      TEXT
  scraped_at           TIMESTAMP
```

## Testing Decisions

**What makes a good test**: Tests verify external behavior at module boundaries — given this input, produce this output. Tests do not assert on internal implementation details. Tests are fast, deterministic, and require no network access.

**Modules with tests:**
- `scraper/parser.py` — tested with pytest against saved HTML fixtures in `scraper/fixtures/`. Tests assert that given a known HTML snapshot, the parser returns a list of dicts with the correct field values.
- dbt models — tested with dbt's built-in schema tests: `not_null` and `unique` on `stg_listings.id`, `not_null` on `int_listing_skills.skill`, row count warnings on mart models if zero rows are returned.

**Not tested:**
- `browser.py` — Playwright context behavior validated implicitly by the full pipeline run; config constants (e.g. `BOT_CHALLENGE_RETRIES`) are asserted in `tests/test_scraper_config.py`
- `loader.py` — validated by idempotent pipeline runs producing no duplicates
- Streamlit dashboard — validated manually via the live deployment

## Out of Scope

- LinkedIn, Indeed, Glassdoor, or any job board that prohibits scraping in its ToS
- Salary parsing beyond capturing the raw salary string (parsing happens in dbt with best-effort regex)
- NLP-based skill extraction (skills matched via deterministic keyword lookup only)
- User authentication or personalization on the dashboard
- Email or Slack alerting on pipeline failures
- Historical backfill beyond what is collected during normal weekly runs
- Mobile-optimized dashboard layout
- Automated browser-based testing of the Streamlit app

## Further Notes

- We Work Remotely categories to scrape: "Programming" and "Data Science" only. Max 1 page per category per run (single-page listing format — all current listings appear on one page).
- The week-over-week trend chart is the hero visualization for interviews — build and polish it first after the pipeline is stable.
- Salary data will be sparse (many WWR listings omit salary). The dashboard salary view must display a data coverage percentage so the chart is not misleading.
- Skills seed includes a `category` column so the Skill Rankings chart can be grouped/colored by category (language, orchestration, warehouse, etc.).
- Local development uses a `.env` file with DATABASE_URL and individual Neon connection vars. The `.env.example` file documents required variables without values.
- The GitHub Actions workflow uses `workflow_dispatch` in addition to the cron schedule so the pipeline can be triggered manually for demos.
