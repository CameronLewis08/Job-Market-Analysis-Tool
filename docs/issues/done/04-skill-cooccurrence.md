# Issue 4: Skill Co-occurrence

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/5
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../../prd.md)

## What to build

Add skill co-occurrence analysis end-to-end: a dbt mart that counts how often pairs of skills appear in the same listing, and a Streamlit dashboard tab that displays the results as a heatmap. After this slice, a user can see which tool combinations employers most commonly require together (e.g., "if a job wants Spark, it also wants...").

## Acceptance criteria

- [x] `dbt/models/marts/mart_skill_cooccurrence.sql` produces one row per (skill_a, skill_b) pair where skill_a < skill_b alphabetically, with a co-occurrence count column
- [x] Only skill pairs with co-occurrence count >= 2 are included (to avoid noise)
- [x] `dbt run && dbt test` passes with no failures including the new model
- [x] `dashboard/app.py` Tab 5 displays a heatmap of skill co-occurrence counts
- [x] Heatmap axes are labeled with skill names, color intensity represents co-occurrence count
- [x] Tab 5 includes a minimum co-occurrence threshold slider to filter noise

## Progress note (2026-05-04)

Issue complete. `dbt run --project-dir dbt --profiles-dir dbt` and
`dbt test --project-dir dbt --profiles-dir dbt` both passed
(`PASS=5` models, `PASS=16` tests, `ERROR=0`).

Files added/changed:
- `dbt/models/marts/mart_skill_cooccurrence.sql`: generates deduplicated `(skill_a, skill_b)` pairs with `skill_a < skill_b`, counts shared listings, and filters to `cooccurrence_count >= 2`
- `dbt/models/marts/schema.yml`: adds schema tests for the new mart columns
- `dashboard/app.py`: implements Tab 5 query + minimum threshold slider + Plotly heatmap rendering
- `dashboard/helpers.py`: adds `filter_cooccurrence` and `build_cooccurrence_matrix` helper functions for threshold filtering and symmetric heatmap matrix construction
- `tests/test_skill_cooccurrence.py`: adds unit tests for the new helper behavior

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
