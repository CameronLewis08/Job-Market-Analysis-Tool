# Issue 1: Project Foundation & Neon Setup

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/2
> Type: HITL

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Set up the project foundation: repository structure, Python dependencies, environment variable configuration, and the `raw_listings` table on a Neon PostgreSQL database. After this slice, a developer can clone the repo, copy `.env.example` to `.env`, fill in their Neon credentials, and have a working database ready to receive scraper output.

## Acceptance criteria

- [x] Repo directory structure exists: `scraper/`, `dbt/`, `dashboard/`, `.github/workflows/`, `tests/`
- [x] `requirements.txt` includes: selenium, beautifulsoup4, psycopg2-binary, python-dotenv, dbt-postgres, streamlit, plotly, pandas, pytest
- [x] `.env.example` documents all required environment variables: `DATABASE_URL`, `NEON_HOST`, `NEON_DB`, `NEON_USER`, `NEON_PASSWORD`
- [x] `.gitignore` excludes `.env`, `__pycache__`, `.dbt/`
- [x] `raw_listings` table exists on Neon with columns: `id VARCHAR PRIMARY KEY`, `title VARCHAR NOT NULL`, `company VARCHAR`, `category VARCHAR`, `date_posted DATE`, `url VARCHAR`, `location_restriction VARCHAR`, `salary_raw VARCHAR`, `description_raw TEXT`, `scraped_at TIMESTAMP`
- [x] Neon dev branch created and separate from the production branch

## Blocked by

None — can start immediately
