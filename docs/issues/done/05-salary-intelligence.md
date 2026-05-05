# Issue 5: Salary Intelligence

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/6
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../../prd.md)

## What to build

Add salary intelligence end-to-end: a dbt mart that extracts and aggregates salary data from the raw `salary_raw` field, and a Streamlit dashboard tab that shows salary ranges by skill alongside a data coverage percentage. After this slice, a user can see which skills correlate with higher pay, with clear visibility into how much of the data actually includes salary information.

## Acceptance criteria

- [x] `dbt/models/marts/mart_skill_salary.sql` extracts numeric salary values from `salary_raw` using regex, produces min/avg/max salary per skill
- [x] Mart includes a `coverage_pct` column: percentage of total listings that had a parseable salary value
- [x] Listings with no parseable salary are excluded from aggregations but counted in coverage denominator
- [x] `dbt run && dbt test` passes with no failures including the new model
- [x] `dashboard/app.py` Tab 2 displays a bar chart of average salary by skill
- [x] Tab 2 shows a "Data coverage: X% of listings include salary" metric above the chart
- [x] Tab 2 respects the global date range filter in the sidebar

## Progress note (2026-05-04)

Issue complete. `dbt run --project-dir dbt --profiles-dir dbt` and
`dbt test --project-dir dbt --profiles-dir dbt` both passed
(`PASS=7` models, `PASS=22` tests, `ERROR=0`).

Files added/changed:
- `dbt/models/marts/mart_skill_salary.sql`: parses salary tokens via regex (including `k` suffix handling), aggregates min/avg/max salary by skill, and computes global salary coverage percentage
- `dbt/models/marts/schema.yml`: adds schema tests for `mart_skill_salary`
- `dashboard/app.py`: implements Tab 2 salary chart, coverage metric, and date-range-aware query

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
