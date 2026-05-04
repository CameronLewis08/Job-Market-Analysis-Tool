# Issue 4: Skill Co-occurrence

> GitHub Issue: https://github.com/CameronLewis08/Job-Market-Analysis-Tool/issues/5
> Type: AFK

## Parent

[PRD: Job Market Analysis Tool](../prd.md)

## What to build

Add skill co-occurrence analysis end-to-end: a dbt mart that counts how often pairs of skills appear in the same listing, and a Streamlit dashboard tab that displays the results as a heatmap. After this slice, a user can see which tool combinations employers most commonly require together (e.g., "if a job wants Spark, it also wants...").

## Acceptance criteria

- [ ] `dbt/models/marts/mart_skill_cooccurrence.sql` produces one row per (skill_a, skill_b) pair where skill_a < skill_b alphabetically, with a co-occurrence count column
- [ ] Only skill pairs with co-occurrence count >= 2 are included (to avoid noise)
- [ ] `dbt run && dbt test` passes with no failures including the new model
- [ ] `dashboard/app.py` Tab 5 displays a heatmap of skill co-occurrence counts
- [ ] Heatmap axes are labeled with skill names, color intensity represents co-occurrence count
- [ ] Tab 5 includes a minimum co-occurrence threshold slider to filter noise

## Blocked by

[Issue 2: Skill Frequency — Full Pipeline Tracer Bullet](./02-skill-frequency-tracer-bullet.md)
