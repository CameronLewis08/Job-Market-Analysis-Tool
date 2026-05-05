# Issue 3: Week-over-Week Skill Trends

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/4
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Add the week-over-week skill trend capability end-to-end: a dbt mart that aggregates listing counts by week and skill, and a Streamlit dashboard tab that plots the trend lines with a multi-skill selector. After this slice, a user can select two or more skills (e.g., dbt vs Airflow vs Spark) and see their relative demand over time on a single line chart.

## Acceptance criteria

- [x] `dbt/models/marts/mart_weekly_trends.sql` produces one row per (week, skill) with a listing count column
- [ ] `dbt run && dbt test` passes with no failures including the new model — **blocked: needs Neon DB credentials (HITL)**
- [x] `dashboard/app.py` Tab 4 displays a line chart of skill demand over time
- [x] Tab 4 includes a multi-select widget to choose which skills to compare
- [x] Chart x-axis is week (ISO week or Monday date), y-axis is listing count
- [x] Tab 4 respects the global date range filter in the sidebar

## Progress note (2026-05-04)

All AFK-executable criteria complete.

Files added/changed:
- `dbt/models/marts/mart_weekly_trends.sql`: groups `int_listing_skills` by `date_trunc('week', date_posted)`, skill, skill_category; counts distinct listing IDs
- `dbt/models/marts/schema.yml`: added `mart_weekly_trends` with not_null tests on week_start, skill, listing_count
- `dashboard/helpers.py`: `filter_weekly_trends(df, skills)` and `top_skills(df, n)` helpers (6 tests, all passing)
- `dashboard/__init__.py`: package init
- `dashboard/app.py`: Tab 4 fully implemented — queries `mart_weekly_trends`, defaults to top-5 skills, multi-select for skill comparison, line chart via plotly

Remaining blocker: `dbt run && dbt test` needs live Neon credentials (HITL).

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
