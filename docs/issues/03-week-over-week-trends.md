# Issue 3: Week-over-Week Skill Trends

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/4
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Add the week-over-week skill trend capability end-to-end: a dbt mart that aggregates listing counts by week and skill, and a Streamlit dashboard tab that plots the trend lines with a multi-skill selector. After this slice, a user can select two or more skills (e.g., dbt vs Airflow vs Spark) and see their relative demand over time on a single line chart.

## Acceptance criteria

- [ ] `dbt/models/marts/mart_weekly_trends.sql` produces one row per (week, skill) with a listing count column
- [ ] `dbt run && dbt test` passes with no failures including the new model
- [ ] `dashboard/app.py` Tab 4 displays a line chart of skill demand over time
- [ ] Tab 4 includes a multi-select widget to choose which skills to compare
- [ ] Chart x-axis is week (ISO week or Monday date), y-axis is listing count
- [ ] Tab 4 respects the global date range filter in the sidebar

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
