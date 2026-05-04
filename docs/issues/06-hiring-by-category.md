# Issue 6: Hiring by Category

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/7
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Add hiring-by-category analysis end-to-end: a dbt mart that aggregates listing counts by We Work Remotely category over time, and a Streamlit dashboard tab displaying a bar chart of hiring volume by category. After this slice, a user can see which job categories (Programming, Data Science) are posting the most data engineering roles.

## Acceptance criteria

- [ ] `dbt/models/marts/mart_industry_hiring.sql` produces one row per (category, week) with a listing count column
- [ ] `dbt run && dbt test` passes with no failures including the new model
- [ ] `dashboard/app.py` Tab 3 displays a bar chart of listing volume by category
- [ ] Tab 3 respects the global date range filter in the sidebar

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
