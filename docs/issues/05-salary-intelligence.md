# Issue 5: Salary Intelligence

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/6
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Add salary intelligence end-to-end: a dbt mart that extracts and aggregates salary data from the raw `salary_raw` field, and a Streamlit dashboard tab that shows salary ranges by skill alongside a data coverage percentage. After this slice, a user can see which skills correlate with higher pay, with clear visibility into how much of the data actually includes salary information.

## Acceptance criteria

- [ ] `dbt/models/marts/mart_skill_salary.sql` extracts numeric salary values from `salary_raw` using regex, produces min/avg/max salary per skill
- [ ] Mart includes a `coverage_pct` column: percentage of total listings that had a parseable salary value
- [ ] Listings with no parseable salary are excluded from aggregations but counted in coverage denominator
- [ ] `dbt run && dbt test` passes with no failures including the new model
- [ ] `dashboard/app.py` Tab 2 displays a bar chart of average salary by skill
- [ ] Tab 2 shows a "Data coverage: X% of listings include salary" metric above the chart
- [ ] Tab 2 respects the global date range filter in the sidebar

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
