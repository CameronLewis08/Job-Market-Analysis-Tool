# Issue 6: Hiring by Category

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/7
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../../prd.md)

## What to build

Add hiring-by-category analysis end-to-end: a dbt mart that aggregates listing counts by We Work Remotely category over time, and a Streamlit dashboard tab displaying a bar chart of hiring volume by category. After this slice, a user can see which job categories (Programming, Data Science) are posting the most data engineering roles.

## Acceptance criteria

- [x] `dbt/models/marts/mart_industry_hiring.sql` produces one row per (category, week) with a listing count column
- [x] `dbt run && dbt test` passes with no failures including the new model
- [x] `dashboard/app.py` Tab 3 displays a bar chart of listing volume by category
- [x] Tab 3 respects the global date range filter in the sidebar

## Progress note (2026-05-04)

Issue complete. `dbt run --project-dir dbt --profiles-dir dbt` and
`dbt test --project-dir dbt --profiles-dir dbt` both passed
(`PASS=7` models, `PASS=22` tests, `ERROR=0`).

Files added/changed:
- `dbt/models/marts/mart_industry_hiring.sql`: builds weekly listing counts by category
- `dbt/models/marts/schema.yml`: adds schema tests for `mart_industry_hiring`
- `dashboard/app.py`: implements Tab 3 category volume bar chart with sidebar date filtering

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
